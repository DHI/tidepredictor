FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

# Create a new user named tide and add to the sudo group
RUN useradd -m -s /bin/bash tide && echo "tide:password" | chpasswd \
    && usermod -aG sudo tide

USER tide

ADD . /home/tide

ENV PATH=$PATH:/home/tide/.local/bin

WORKDIR /home/tide

RUN uv sync --no-dev

RUN uv tool install .



# Test data, replace with proper constituents
RUN mkdir -p ~/.local/share/tidepredictor; cp ~/tests/data/*.nc ~/.local/share/tidepredictor

CMD ["bash"]
