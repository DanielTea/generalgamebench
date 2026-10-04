"""Local cached VLM JSONL agent; persistent weights, fresh image on every action."""

import base64
import io
import json
import os
import sys

from model_prompt import format_prompt


def main():
    # Only cached weights are permitted in this worker.
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    output = os.fdopen(os.dup(sys.stdout.fileno()), "w", buffering=1)
    os.dup2(sys.stderr.fileno(), sys.stdout.fileno())
    import mlx.core as mx
    from mlx_vlm import generate, load
    from mlx_vlm.prompt_utils import apply_chat_template
    from PIL import Image

    model, processor = load(sys.argv[1])
    output.write('{"ready":true}\n')
    for line in sys.stdin:
        obs = json.loads(line)
        prompt = format_prompt(obs)
        formatted = apply_chat_template(
            processor, model.config, prompt, num_images=1, enable_thinking=False
        )
        image = Image.open(io.BytesIO(base64.b64decode(obs["image_png"]))).convert("RGB")
        result = generate(
            model,
            processor,
            formatted,
            image=[image],
            max_tokens=128,
            temperature=0.0,
            verbose=False,
        )
        mx.synchronize()
        text = result.text.strip()
        if "--debug" in sys.argv:
            print(repr(text), file=sys.stderr, flush=True)
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        # No forgiving regex that could turn invalid text into an invented action.
        try:
            value = json.loads(text)
            if set(value) != {"action"} or type(value["action"]) is not int:
                raise ValueError("Invalid action")
            reply = {"nonce": obs["nonce"], "action": value["action"]}
        except (ValueError, TypeError):
            reply = {"nonce": obs["nonce"], "action": None}
        output.write(json.dumps(reply) + "\n")


if __name__ == "__main__":
    main()
