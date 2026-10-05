/* Optional Linux diagnostic. Never loaded during scored model runs. */
#define _GNU_SOURCE
#include <execinfo.h>
#include <signal.h>
#include <sys/time.h>
#include <unistd.h>

static void trace_stack(int signal_number)
{
    (void)signal_number;
    void *frames[80];
    const char message[] = "\nNative engine stack after 25 seconds:\n";
    write(STDERR_FILENO, message, sizeof(message) - 1);
    backtrace_symbols_fd(frames, backtrace(frames, 80), STDERR_FILENO);
}

void gg_trace_arm(void)
{
    struct sigaction handler = {0};
    handler.sa_handler = trace_stack;
    handler.sa_flags = SA_RESTART;
    sigemptyset(&handler.sa_mask);
    sigaction(SIGALRM, &handler, 0);
    struct itimerval timer = {{25, 0}, {25, 0}};
    setitimer(ITIMER_REAL, &timer, 0);
}

void gg_trace_stop(void)
{
    struct itimerval timer = {{0, 0}, {0, 0}};
    setitimer(ITIMER_REAL, &timer, 0);
}
