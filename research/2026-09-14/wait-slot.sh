# sourced helper (2026-09-23): block until fewer than MAX_JOBS (default 5) research compute processes are running,
# so independent queues together stay within the 25 % CPU cap. Random start jitter reduces two lanes taking one slot.
wait_slot() {
  sleep $((RANDOM % 20))
  while [ "$(pgrep -fc 'python 08-design.py|python 24-hopfield.py|node .*vite-node (08-eval|02-nl-amp|22-b4f-amp|23-robust|16-basin)')" -ge "${MAX_JOBS:-5}" ]; do sleep 20; done
}
