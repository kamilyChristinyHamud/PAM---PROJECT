
#para gerar par de chaves
if [ ! -f /vault/ca_key ]; then
    echo "=== Gerando chaves da CA ==="
    ssh-keygen -t rsa -b 4096 -f /vault/ca_key -N "" -C "CA@pam-system"
    echo "=== Chaves da CA geradas com sucesso! ==="
fi

echo "=== Vault (CA) pronto e aguardando ==="
tail -f /dev/null
