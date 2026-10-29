# Acortador de enlaces en AWS (S3 + EC2 + DynamoDB)

```
Navegador → S3 (interfaz) → POST /shorten → EC2 (FastAPI) → DynamoDB
Navegador → http://<ip-ec2>:8000/<uuid> → EC2 consulta DynamoDB → 307 → URL original
```

Estructura: `backend/` (API) y `frontend/` (HTML/CSS/JS).

## 1. Repositorio

```bash
cd acortador-aws
git init && git add . && git commit -m "Acortador de enlaces"
git branch -M main
git remote add origin https://github.com/<usuario>/acortador-aws.git
git push -u origin main
```

## 2. DynamoDB

Consola → DynamoDB → Create table: nombre `short_links`, partition key `short_code` (String), capacidad On-demand.

## 3. Rol IAM

1. IAM → Policies → Create policy → JSON (cambia REGION y ID_DE_CUENTA):

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["dynamodb:PutItem", "dynamodb:GetItem"],
    "Resource": "arn:aws:dynamodb:REGION:ID_DE_CUENTA:table/short_links"
  }]
}
```

2. IAM → Roles → Create role → AWS service → EC2 → adjunta esa política → nombre `acortador-ec2-role`.

## 4. EC2

Launch instance: Amazon Linux 2023, t2/t3.micro, crea un key pair. En el Security Group:

| Tipo | Puerto | Origen |
|---|---|---|
| SSH | 22 | My IP |
| Custom TCP | 8000 | 0.0.0.0/0 |

En *Advanced details → IAM instance profile* elige `acortador-ec2-role`. Anota la IP pública.

## 5. Backend en la EC2

```bash
ssh -i llave.pem ec2-user@<ip-publica-ec2>
sudo dnf install -y python3 python3-pip git
git clone https://github.com/<usuario>/acortador-aws.git
cd acortador-aws/backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env && nano .env
```

Valores del `.env`: `AWS_REGION`, `DYNAMODB_TABLE=short_links`, `PUBLIC_BASE_URL=http://<ip-publica-ec2>:8000`, `CORS_ORIGINS=<URL del sitio S3, paso 6>`.

Servicio permanente:

Crea el archivo con `sudo nano /etc/systemd/system/acortador.service` y pega:

```ini
[Unit]
Description=Acortador de enlaces (FastAPI + Uvicorn)
After=network.target

[Service]
User=ec2-user
WorkingDirectory=/home/ec2-user/acortador-aws/backend
EnvironmentFile=/home/ec2-user/acortador-aws/backend/.env
ExecStart=/home/ec2-user/acortador-aws/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Luego actívalo:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now acortador
sudo systemctl status acortador
```

Comprueba que responde en `http://<ip-publica-ec2>:8000/docs`.

## 6. Interfaz en S3

1. Edita `frontend/config.js` con `API_URL: "http://<ip-publica-ec2>:8000"` y haz push.
2. S3 → Create bucket (nombre único). Desmarca *Block all public access*.
3. Sube `index.html`, `styles.css`, `app.js`, `config.js`.
4. Properties → Static website hosting → Enable, Index document `index.html`.
5. Permissions → Bucket policy (cambia NOMBRE_DEL_BUCKET):

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": "*",
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::NOMBRE_DEL_BUCKET/*"
  }]
}
```

6. Copia el *Bucket website endpoint* (`http://...s3-website-<región>.amazonaws.com`), ponlo en `CORS_ORIGINS` del `.env` de la EC2 (sin barra final) y ejecuta `sudo systemctl restart acortador`.

El sitio de S3 va por HTTP, por eso la API también va por HTTP.

## 7. Pruebas

1. Abre el sitio de S3, acorta `https://www.example.com/articulos/arquitectura-cloud` y revisa el registro en DynamoDB (Explore items).
2. Copia y abre el enlace corto: debe llevarte a la URL original.
   `curl -i http://<ip-ec2>:8000/<uuid>` muestra `307` y `Location`.
3. UUID inexistente: `curl -i http://<ip-ec2>:8000/00000000-0000-0000-0000-000000000000` devuelve 404.
4. Información: `curl http://<ip-ec2>:8000/urls/<uuid>`.
5. Persistencia: `sudo systemctl restart acortador` y abre de nuevo el mismo enlace.

## 8. Entrega

Enlace del repositorio y un video que muestre: la tabla de DynamoDB, el rol IAM y su política, la EC2 con su Security Group y `systemctl status`, el bucket S3 y la demo de las pruebas anteriores.

## API

| Método | Ruta | Respuesta |
|---|---|---|
| POST | `/shorten` | 201 con `short_code`, `original_url`, `short_url` |
| GET | `/{short_code}` | 307 a la URL original, o 404 |
| GET | `/urls/{short_code}` | JSON con `short_code`, `original_url`, `created_at`, o 404 |
