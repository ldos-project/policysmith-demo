# Vulcan Tutorial at the 2026 LDOS PhD Research School
- Link to [Google slides](https://docs.google.com/presentation/d/1OknSVNHAMNUFhOmBR4Pgj78rnCqo7dwIkefcZ9w6-Lw/edit?usp=sharing)
- This branch (master) contains the started code used for the tutorial.
- [leaderboard branch](https://github.com/ldos-project/vulcan-demo/tree/leaderboard): code for the live leaderboard used during the tutorial.
- [gh-pages](https://github.com/ldos-project/vulcan-demo/tree/gh-pages): snapshot of the final leaderboard after the tutorial. Can be viewed online at: https://ldos-project.github.io/vulcan-demo/ 

## Setup instructions

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

## Next steps
Implement a simple evolve.py to implement heuristics, and then use `python3 full_eval.py` to evaluate the heuristic you found on all traces and submit them to be featured in the leaderboard!

#  Acknowledgements
This material is based upon work supported by the U.S. National Science Foundation (NSF) under Grant Number 2326576. Any opinions, findings and conclusions or recommendations expressed in this material do not necessarily reflect the views of the U.S. National Science Foundation. The presentor of this tutorial (Dwivedula) was also supported with an Amazon AI Fellowship
