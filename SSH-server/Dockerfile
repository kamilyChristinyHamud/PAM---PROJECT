FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    openssh-server \
    sudo \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir /var/run/sshd

RUN useradd -m -s /bin/bash sshuser && \
    echo "sshuser:password123" | chpasswd && \
    mkdir -p /home/sshuser/.ssh && \
    chmod 700 /home/sshuser/.ssh && \
    chown -R sshuser:sshuser /home/sshuser/.ssh

COPY sshd_config /etc/ssh/sshd_config
COPY setup.sh /setup.sh
RUN chmod +x /setup.sh

EXPOSE 22

CMD ["/setup.sh"]
