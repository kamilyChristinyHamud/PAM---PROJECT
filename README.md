PAM - Privileged Access Management

Este trabalho implementa uma arquitetura PAM usando certificados digitais temporários para autenticar conexões SSH. O sistema roda com três elementos principais, todos em containers Docker, que trocam informações numa rede própria.

O foco é garantir acesso seguro a servidores privilegiados, e para isso foi implementado:

- Autenticação MFA
- Certificados digitais com validade de 10 minutos
- Autoridade Certificadora (CA)
- Eliminação completa do uso de senha

Arquitetura do Sistema

O sistema é composto por três containers que se comunicam numa rede Docker privada chamada `pam-network`:

| Container | O que faz |

| Vault | É a Autoridade Certificadora (CA). Gera o par de chaves RSA 4096 e assina os certificados.
| SSH-Server | Servidor SSH configurado para aceitar conexões **somente por certificado**, sem senha.
| Signer | Interface web feita em Flask. Valida o MFA e pede pro Vault assinar o certificado.

Estrutura de Pastas:

pam-project/
├── vault/
│   ├── Dockerfile
│   └── entrypoint.sh
│
├── ssh-server/
│   ├── Dockerfile
│   ├── sshd_config
│   └── setup.sh
│
└── signer/
    ├── Dockerfile
    ├── requirements.txt
    └── app.py

Cada subdiretório tem seus próprios arquivos de configuração e Dockerfiles, facilitando a manutenção.

--> Como Executar

Pré-requisitos
- Docker instalado e rodando
- Portas `2222` e `5000` disponíveis

1. Criar a rede Docker
bash
docker network create pam-network

2. Subir o Vault
bash
cd vault
docker build -t pam-vault .
docker run -d --name vault --network pam-network \
  -v ~/pam-project/vault/data:/vault \
  pam-vault

3. Subir o SSH-Server
bash
cd ../ssh-server
docker build -t pam-ssh-server .
docker run -d --name ssh-server --network pam-network \
  -v ~/pam-project/vault/data:/ca-keys:ro \
  -p 2222:22 \
  pam-ssh-server

4. Subir o Signer
bash
cd ../signer
docker build -t pam-signer .
docker run -d --name signer --network pam-network \
  -p 5000:5000 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  pam-signer

5. Verificar se está tudo rodando
bash
docker ps

Os três containers ("vault", "ssh-server", "signer') devem aparecer com status "Up".


--> Como Usar

Acesse "http://localhost:5000" pelo navegador e siga os passos:

--> Passo 1 — Gerar o par de chaves SSH

Execute no terminal:
ssh-keygen -t rsa -b 4096 -f ~/.ssh/pam_key -N ""
cat ~/.ssh/pam_key.pub

Isso gera dois arquivos: a chave privada `pam_key` e a chave pública `pam_key.pub`. Copie o conteúdo da chave pública.

Passo 2 — Configurar o MFA

Insira seu nome de usuário e clique em *Gerar QR Code MFA*. Escaneie o QR Code com o Google Authenticator no celular.

--> Passo 3 — Solicitar o Certificado

Preencha seu usuário, o código de 6 dígitos do autenticador e cole sua chave pública. Clique em *Solicitar Certificado*.

Passo 4 — Salvar o certificado
cat > ~/.ssh/pam_key-cert.pub << 'EOF'
--> cole aqui o certificado gerado pela interface
EOF

--> Passo 5 — Conectar via SSH
ssh -i ~/.ssh/pam_key -o IdentitiesOnly=yes -o PreferredAuthentications=publickey -p 2222 sshuser@localhost

--> O certificado expira em 10 minutos. Após esse período, repita a partir do Passo 3.

Observações:

Durante o desenvolvimento, identificamos um ponto de melhoria: os segredos MFA ficam guardados em memória (dicionário Python), o que não é indicado para produção. O ideal seria armazená-los em um banco de dados criptografado.

Autoras:

Kamily Hamud — [LinkedIn](https://www.linkedin.com/in/kamily-hamud-349b06252/) | [TryHackMe](https://tryhackme.com/p/kamily.christiny)

Carolina Greiffo.
