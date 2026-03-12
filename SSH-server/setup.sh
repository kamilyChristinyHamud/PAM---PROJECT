
echo "=== Aguardando chave pública da CA ==="
while [ ! -f /ca-keys/ca_key.pub ]; do
    echo "Esperando CA"
    sleep 2
done

cp /ca-keys/ca_key.pub /etc/ssh/ca_key.pub
echo "=== Chave da CA configurada ==="
echo "=== SSH Server pronto para receber conexões ==="

/usr/sbin/sshd -D