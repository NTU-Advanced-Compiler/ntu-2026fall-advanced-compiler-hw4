# HW4 homework image.
#
# Built on the HW1 image so the environment students already know is
# unchanged: Ubuntu 22.04, user `student`, repository at /home/student/hw.
# The difference is that the Bril tools are already installed, because
# installing them was the HW1 exercise and is not what HW4 grades.
#
# Build from the repository root, with the bril submodule initialized:
#   git submodule update --init --recursive
#   docker build -t acd-hw4:2026 .
#
# The base image is pinned by digest so the environment is reproducible.
FROM pipibear1015/acd-hw1:2026@sha256:d1d10b955813d2fdd9278e490293ce79641826c5a91d1fd5e98ecd9eafdf759b

USER student

# The pinned Bril checkout (submodule revision
# 4029dd7b6440074bc4dd5557022848ef378f978a).
COPY --chown=student:student bril /opt/bril

# Pinned tool versions. bril-txt declares `lark-parser`, not `lark`; both
# are pinned so a future release cannot change the parser under us.
RUN python3 -m pip install --user --no-warn-script-location \
        flit==3.9.0 lark-parser==0.12.0 \
 && cd /opt/bril/bril-txt && flit install --symlink --user \
 && cd /opt/bril && deno install brili.ts

# Fail the build if any tool is missing or broken.
RUN printf '@main {\n  a: int = const 2;\n  b: int = add a a;\n  print b;\n}\n' \
        > /tmp/smoke.bril \
 && test "$(bril2json < /tmp/smoke.bril | brili)" = "4" \
 && bril2json < /tmp/smoke.bril | bril2txt > /dev/null \
 && rm -f /tmp/smoke.bril

WORKDIR /home/student/hw
CMD ["/bin/bash"]
