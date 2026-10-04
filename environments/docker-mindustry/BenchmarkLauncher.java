// SPDX-License-Identifier: GPL-3.0-only
import arc.*;
import arc.backend.sdl.*;
import arc.files.*;
import arc.input.*;
import arc.math.*;
import arc.mock.*;
import arc.util.*;
import mindustry.*;
import mindustry.content.*;
import mindustry.desktop.*;
import mindustry.game.*;
import mindustry.gen.*;
import java.io.*;
import static mindustry.Vars.*;

public class BenchmarkLauncher extends DesktopLauncher {
    static final BufferedReader commands = new BufferedReader(new InputStreamReader(System.in));
    boolean ready;
    int initialCopper;
    static class BenchInput extends MockInput {
        int x=480, y=320;
        public int mouseX(){return x;}
        public int mouseY(){return y;}
        public int mouseX(int p){return x;}
        public int mouseY(int p){return y;}
    }
    BenchInput input;
    public BenchmarkLauncher(){super(new String[0]);}
    public static void main(String[] args) {
        System.setProperty("nodiscord", "true");
        new SdlApplication(new BenchmarkLauncher(), new SdlConfig(){{
            width=960; height=640; maximized=false; resizable=false;
            disableAudio=true; vSyncEnabled=false; coreProfile=true;
            glVersions=new int[][]{{3,3},{3,2},{2,1}};
        }});
    }
    int copper(){
        int amount=player.core()==null ? 0 : player.core().items.get(Items.copper);
        if(!player.dead() && player.unit().stack.item==Items.copper) amount+=player.unit().stack.amount;
        return amount;
    }
    void tick(boolean updateGlobal){
        if(updateGlobal) Time.updateGlobal();
        super.update();
        input.getKeyboard().postUpdate();
    }
    @Override public void update(){
        if(!clientLoaded){super.update();return;}
        try {
            if(!ready){
                Core.settings.put("fpscap",0); Core.settings.put("showfps",false);
                Core.settings.put("doubletapmine",false); Core.settings.put("savecreate",false);
                Core.settings.put("effects",false); Core.settings.put("screenshake",0);
                input=new BenchInput();
                for(var processor: Core.input.getInputProcessors()) input.addProcessor(processor);
                Core.input=input;
                Time.setDeltaProvider(()->1f); Time.setInternalTime(0);
                long seed=Long.parseLong(System.getenv().getOrDefault("GGBENCH_SEED","71"));
                Mathf.rand.setSeed(seed);
                logic.reset();
                var map=maps.loadInternalMap("serpulo/groundZero");
                if(map==null) throw new RuntimeException("Map missing; maps="+maps.all());
                var rules=Gamemode.survival.apply(map.rules());
                world.loadMap(map,rules); state.rules=rules;
                logic.play();
                player.team(state.rules.defaultTeam);
                while(Core.scene.getDialog()!=null) Core.scene.getDialog().hide();
                renderer.setScale(3);
                for(int i=0;i<120;i++) tick(true);
                initialCopper=copper(); ready=true;
            }
            ScreenUtils.saveScreenshot(new Fi(System.getenv("GGBENCH_CAPTURE")));
            System.out.println("GGBENCH {\"copper\":"+(copper()-initialCopper)+",\"dead\":"+player.dead()+"}");
            String line=commands.readLine();
            if(line==null) { Core.app.exit(); return; }
            int action=Integer.parseInt(line);
            for(KeyCode key:new KeyCode[]{KeyCode.w,KeyCode.a,KeyCode.s,KeyCode.d,KeyCode.mouseLeft}) input.getKeyboard().keyUp(key);
            if(action>=1 && action<=4) input.getKeyboard().keyDown(new KeyCode[]{KeyCode.w,KeyCode.d,KeyCode.s,KeyCode.a}[action-1]);
            if(action>=5 && action<=8){
                int[] dx={0,32,0,-32},dy={32,0,-32,0};
                input.x=Mathf.clamp(input.x+dx[action-5],0,959); input.y=Mathf.clamp(input.y+dy[action-5],0,639);
            }
            if(action==9) input.getKeyboard().keyDown(KeyCode.mouseLeft);
            for(int i=0;i<6;i++) tick(i>0);
        }catch(Exception e){throw new RuntimeException(e);}
    }
}
