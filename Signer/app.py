from flask import Flask, request, jsonify, render_template_string
import subprocess
import os
import pyotp
import qrcode
import io
import base64
import tempfile

app = Flask(__name__)

mfa_secrets = {}

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>SecureAccess PAM</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
        
        * { 
            margin: 0; 
            padding: 0; 
            box-sizing: border-box; 
        }
        
        body { 
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #1a1a1a 0%, #2a2a2a 50%, #353535 100%);
            min-height: 100vh;
            padding: 40px 20px;
            color: #ffffff;
        }
        
        .main-container {
            max-width: 1000px;
            margin: 0 auto;
        }
        
        .hero {
            text-align: center;
            margin-bottom: 50px;
            animation: fadeInDown 0.8s ease;
        }
        
        .hero h1 {
            font-size: 3.5em;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 10px;
            text-shadow: 
                -1px -1px 0 #8b3ab5,
                1px -1px 0 #8b3ab5,
                -1px 1px 0 #8b3ab5,
                1px 1px 0 #8b3ab5,
                0 0 10px rgba(139, 58, 181, 0.5);
        }
        
        .hero p {
            font-size: 1.2em;
            color: #d1d5db;
            font-weight: 300;
        }
        
        .card {
            background: #2d2d2d;
            border: 1px solid #444444;
            border-radius: 20px;
            padding: 35px;
            margin: 30px 0;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            animation: fadeInUp 0.8s ease;
        }
        
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 48px rgba(139, 58, 181, 0.3);
        }
        
        .card-header {
            display: flex;
            align-items: center;
            margin-bottom: 25px;
            padding-bottom: 20px;
            border-bottom: 2px solid rgba(139, 58, 181, 0.3);
        }
        
        .step-number {
            background: linear-gradient(135deg, #ec4899 0%, #f472b6 100%);
            width: 50px;
            height: 50px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5em;
            font-weight: 700;
            margin-right: 20px;
            color: #ffffff;
        }
        
        .card-header h2 {
            font-size: 1.6em;
            font-weight: 600;
            color: #ffffff;
            text-shadow: 
                -1px -1px 0 #8b3ab5,
                1px -1px 0 #8b3ab5,
                -1px 1px 0 #8b3ab5,
                1px 1px 0 #8b3ab5;
        }
        
        .input-group {
            margin: 20px 0;
        }
        
        input[type="text"], textarea {
            width: 100%;
            padding: 15px 20px;
            margin: 10px 0;
            border: 2px solid #8b3ab5;
            border-radius: 12px;
            font-size: 1em;
            background: #1a1a1a;
            color: #ffffff;
            transition: all 0.3s ease;
            font-family: 'Inter', sans-serif;
        }
        
        input[type="text"]::placeholder, textarea::placeholder {
            color: #9ca3af;
        }
        
        input[type="text"]:focus, textarea:focus {
            outline: none;
            border-color: #d946ef;
            background: #1f1f1f;
            box-shadow: 0 0 20px rgba(139, 58, 181, 0.3);
        }
        
        textarea {
            height: 140px;
            font-family: 'Courier New', monospace;
            resize: vertical;
            line-height: 1.6;
        }
        
        .btn {
            background: linear-gradient(135deg, #8b3ab5 0%, #d946ef 100%);
            color: #ffffff;
            padding: 15px 50px;
            border: none;
            border-radius: 12px;
            cursor: pointer;
            font-size: 1.1em;
            font-weight: 600;
            transition: all 0.3s ease;
            margin: 20px auto;
            display: block;
            font-family: 'Inter', sans-serif;
        }
        
        .btn:hover {
            transform: translateY(-3px) scale(1.05);
            box-shadow: 0 8px 30px rgba(139, 58, 181, 0.5);
        }
        
        .btn:active {
            transform: translateY(0) scale(1);
        }
        
        .alert {
            padding: 20px;
            border-radius: 12px;
            margin: 20px 0;
            animation: slideIn 0.5s ease;
        }
        
        .alert-success {
            background: rgba(236, 72, 153, 0.1);
            border: 2px solid rgba(236, 72, 153, 0.3);
            color: #f472b6;
        }
        
        .alert-error {
            background: rgba(255, 82, 82, 0.1);
            border: 2px solid rgba(255, 82, 82, 0.3);
            color: #ff5252;
        }
        
        .alert h3 {
            margin-bottom: 10px;
            font-size: 1.3em;
        }
        
        .code-block {
            background: #0a0a0a;
            color: #ec4899;
            padding: 20px;
            border-radius: 12px;
            margin: 15px 0;
            font-family: 'Courier New', monospace;
            overflow-x: auto;
            border: 1px solid #444444;
            line-height: 1.6;
            font-size: 0.95em;
        }
        
        .qr-wrapper {
            text-align: center;
            margin: 30px 0;
            padding: 30px;
            background: #1f1f1f;
            border-radius: 15px;
            border: 2px dashed rgba(139, 58, 181, 0.3);
        }
        
        .qr-wrapper img {
            max-width: 280px;
            margin: 20px auto;
            display: block;
            background: white;
            padding: 15px;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
        }
        
        .secret-display {
            background: rgba(139, 58, 181, 0.2);
            padding: 20px;
            border-radius: 12px;
            margin: 15px 0;
            font-family: 'Courier New', monospace;
            font-size: 1.3em;
            text-align: center;
            border: 2px solid #8b3ab5;
            color: #d946ef;
            letter-spacing: 3px;
            font-weight: 600;
        }
        
        .info-panel {
            background: #1f1f1f;
            border-left: 4px solid #8b3ab5;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
        }
        
        .info-panel p {
            margin: 10px 0;
            color: #d1d5db;
            line-height: 1.6;
        }
        
        .info-panel ul {
            margin-left: 20px;
            margin-top: 15px;
            color: #d1d5db;
        }
        
        .info-panel li {
            margin: 8px 0;
            line-height: 1.6;
        }
        
        .info-panel strong {
            color: #ec4899;
        }
        
        .loading {
            text-align: center;
            color: #ec4899;
            font-size: 1.1em;
            padding: 20px;
        }
        
        @keyframes fadeInDown {
            from {
                opacity: 0;
                transform: translateY(-30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateX(-20px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
        
        .card:nth-child(1) { animation-delay: 0.1s; }
        .card:nth-child(2) { animation-delay: 0.2s; }
        .card:nth-child(3) { animation-delay: 0.3s; }
    </style>
</head>
<body>
    <div class="main-container">
        <div class="hero">
            <h1>SecureAccess PAM</h1>
            <p>Sistema de Gerenciamento de Acesso Privilegiado</p>
        </div>
        
        <div class="card">
            <div class="card-header">
                <div class="step-number">1</div>
                <h2>Geração do Par de Chaves</h2>
            </div>
            <div class="info-panel">
                <p><strong>Execute o primeiro comando no seu terminal:</strong></p>
            </div>
            <div class="code-block">ssh-keygen -t rsa -b 4096 -f ~/.ssh/pam_key -N ""</div>
            <div class="info-panel">
                <p><strong>Depois execute o segundo comando para visualizar a chave pública:</strong></p>
            </div>
            <div class="code-block">cat ~/.ssh/pam_key.pub</div>
            <div class="info-panel">
                <p>Estes comandos irão gerar e exibir:</p>
                <ul>
                    <li><strong>~/.ssh/pam_key</strong> - Sua chave privada (mantenha segura!)</li>
                    <li><strong>~/.ssh/pam_key.pub</strong> - Sua chave pública (copie o conteúdo exibido)</li>
                </ul>
            </div>
        </div>
        
        <div class="card">
            <div class="card-header">
                <div class="step-number">2</div>
                <h2>Autenticação via MFA</h2>
            </div>
            <p style="margin-bottom: 20px; color: #d1d5db;">Configure a autenticação de dois fatores para seu usuário.</p>
            <div class="input-group">
                <input type="text" id="username" placeholder="Seu nome de usuário">
                <button class="btn" onclick="setupMFA()">Gerar QR Code MFA</button>
            </div>
            <div id="qr-code"></div>
        </div>
        
        <div class="card">
            <div class="card-header">
                <div class="step-number">3</div>
                <h2>Envio da Chave Pública</h2>
            </div>
            <div class="input-group">
                <input type="text" id="user" placeholder="Nome de usuário (igual ao Passo 2)">
                <input type="text" id="mfa-code" placeholder="Código MFA (6 dígitos do app)">
                <textarea id="public-key" placeholder="Cole aqui o conteúdo completo do arquivo ~/.ssh/pam_key.pub"></textarea>
                <button class="btn" onclick="requestCertificate()">Solicitar Certificado</button>
            </div>
            <div id="result"></div>
        </div>
    </div>
    
    <script>
        async function setupMFA() {
            const username = document.getElementById('username').value;
            if (!username) {
                alert('Por favor, digite um nome de usuário');
                return;
            }
            
            const response = await fetch('/setup-mfa', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({username})
            });
            
            const data = await response.json();
            
            document.getElementById('qr-code').innerHTML = 
                `<div class="qr-wrapper">
                    <h3 style="color: #ec4899; margin-bottom: 15px;">MFA Configurado!</h3>
                    <p style="color: #d1d5db; margin-bottom: 20px;">Escaneie o QR Code com Google Authenticator ou Authy:</p>
                    <img src="data:image/png;base64,${data.qr_code}" alt="QR Code">
                    <p style="color: #d1d5db; margin: 20px 0 10px 0;">Ou insira este código manualmente:</p>
                    <div class="secret-display">${data.secret}</div>
                </div>`;
        }
        
        async function requestCertificate() {
            const username = document.getElementById('user').value;
            const mfa_code = document.getElementById('mfa-code').value;
            const public_key = document.getElementById('public-key').value;
            
            if (!username || !mfa_code || !public_key) {
                alert('Por favor, preencha todos os campos');
                return;
            }
            
            document.getElementById('result').innerHTML = '<div class="loading">Processando requisição...</div>';
            
            const response = await fetch('/request-certificate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({username, mfa_code, public_key})
            });
            
            const data = await response.json();
            
            if (data.success) {
                document.getElementById('result').innerHTML = 
                    `<div class="alert alert-success">
                        <h3>Certificado Gerado com Sucesso!</h3>
                        <p><strong>Validade:</strong> ${data.validity}</p>
                    </div>
                    <div class="info-panel">
                        <p><strong>Passo 4: Salvar o certificado</strong></p>
                        <p>Execute este comando para abrir o editor:</p>
                    </div>
                    <div class="code-block">cat > ~/.ssh/pam_key-cert.pub << 'EOF'</div>
                    <div class="info-panel">
                        <p><strong>Depois cole o certificado abaixo:</strong></p>
                    </div>
                    <div class="code-block" style="max-height: 150px; overflow-y: auto;">${data.certificate}</div>
                    <div class="info-panel">
                        <p><strong>Por fim, digite EOF e pressione Enter para finalizar:</strong></p>
                    </div>
                    <div class="code-block">EOF</div>
                    <div class="info-panel">
                        <p><strong>Passo 5: Conectar via SSH</strong></p>
                    </div>
                    <div class="code-block">ssh -i ~/.ssh/pam_key -o IdentitiesOnly=yes -o PreferredAuthentications=publickey -p 2222 sshuser@localhost</div>
                    <div class="info-panel">
                        <p><strong>Atenção:</strong> Este certificado expira em ${data.validity}. Após esse período, você precisará solicitar um novo.</p>
                    </div>`;
            } else {
                document.getElementById('result').innerHTML = 
                    `<div class="alert alert-error">
                        <h3>Erro ao Gerar Certificado</h3>
                        <p>${data.error}</p>
                    </div>`;
            }
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/setup-mfa', methods=['POST'])
def setup_mfa():
    data = request.json
    username = data.get('username')
    
    if not username:
        return jsonify({'success': False, 'error': 'Username obrigatório'})
    
    secret = pyotp.random_base32()
    mfa_secrets[username] = secret
    
    totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=username, 
        issuer_name='PAM System'
    )
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(totp_uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    print(f"[INFO] MFA configurado para usuário: {username}")
    return jsonify({'secret': secret, 'qr_code': qr_base64})

@app.route('/request-certificate', methods=['POST'])
def request_certificate():
    data = request.json
    username = data.get('username')
    mfa_code = data.get('mfa_code')
    public_key = data.get('public_key')
    
    if not username or not mfa_code or not public_key:
        return jsonify({'success': False, 'error': 'Todos os campos são obrigatórios'})
    
    if username not in mfa_secrets:
        return jsonify({'success': False, 'error': 'Configure o MFA primeiro para este usuário'})
    
    totp = pyotp.TOTP(mfa_secrets[username])
    if not totp.verify(mfa_code, valid_window=1):
        print(f"[ERROR] Código MFA inválido para {username}")
        return jsonify({'success': False, 'error': 'Código MFA inválido. Verifique o código no app.'})
    
    print(f"[INFO] MFA validado com sucesso para {username}")
    
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pub', delete=False) as tmp_key:
            tmp_key.write(public_key)
            tmp_key_path = tmp_key.name
        
        subprocess.run([
            'docker', 'cp', tmp_key_path, 'vault:/tmp/user_key.pub'
        ], check=True)
        print(f"[INFO] Chave pública copiada para o Vault")
        
        validity = "+10m"
        subprocess.run([
            'docker', 'exec', 'vault', 'ssh-keygen',
            '-s', '/vault/ca_key',
            '-I', username,
            '-n', 'sshuser',
            '-V', validity,
            '/tmp/user_key.pub'
        ], check=True, capture_output=True)
        print(f"[INFO] Certificado assinado com sucesso para {username}")
        
        result = subprocess.run([
            'docker', 'exec', 'vault', 'cat', '/tmp/user_key-cert.pub'
        ], capture_output=True, text=True, check=True)
        
        certificate = result.stdout.strip()
        os.unlink(tmp_key_path)
        
        print(f"[SUCCESS] Certificado entregue para {username}")
        
        return jsonify({
            'success': True,
            'certificate': certificate,
            'validity': '10 minutos'
        })
        
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Erro ao assinar certificado: {e}")
        return jsonify({'success': False, 'error': f'Erro ao assinar certificado: {str(e)}'})
    except Exception as e:
        print(f"[ERROR] Erro geral: {e}")
        return jsonify({'success': False, 'error': f'Erro: {str(e)}'})

if __name__ == '__main__':
    print("="*50)
    print("PAM Signer Application")
    print("Acesse: http://localhost:5000")
    print("="*50)
    app.run(host='0.0.0.0', port=5000, debug=True)