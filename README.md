# Setup instructions

Run all instructions in the root of this repository
1. Clone submodules: `git submodule update --init --recursive`
2. Install build deps (CMake, GLib, zstd): `./libcachesim/scripts/install_dependency.sh`
3. Create and activate a venv: `python3 -m venv .venv && source .venv/bin/activate`
4. Install Python deps: `pip3 install openai`
5. Set your API key in `llm.py`. To verify the key works, run the following:
    ```bash
    curl https://workshop.dwivedula.dev/v1/chat/completions \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer YOUR_KEY_HERE" \
      -d '{"model": "claude-sonnet", "messages": [{"role": "user", "content": "Hello"}]}'
    ```
6. Run: `cp initial_program.cpp libcachesim/libCacheSim/cache/eviction/cpp/LLMCode.h`
7. Build the evaluator: `mkdir build && cd build && cmake ../  && make -j && cd ../`
8. Download traces:
    ```bash
    mkdir traces && cd traces
    for file in w105 w87 w86 w93 w89 w103 w94 w90 w106 w99; do
        wget https://ftp.pdl.cmu.edu/pub/datasets/twemcacheWorkload/fast23_glcache/cloudphysics/$file.oracleGeneral.bin.zst;
    done
    cd ..  
    ```
9. Run: `python test_evaluator.py`.

# Next steps
Implement a simple evolve.py to implement heuristics, and then use `python3 full_eval.py` to evaluate the heuristic you found on all traces and submit them to be featured in the leaderboard!
