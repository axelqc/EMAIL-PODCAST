from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from email.header import Header
import os
import traceback
from dotenv import load_dotenv
import ibm_db_dbi
from database import get_db_connection  # Reutiliza tu database.py existente

load_dotenv()

app = FastAPI()

# -----------------------------------------------
# CORS – ajusta el origin a tu dominio en producción
# -----------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)

# -----------------------------------------------
# CONFIG SMTP
# -----------------------------------------------
SMTP_SERVER  = os.getenv("SMTP_SERVER")
SMTP_PORT    = int(os.getenv("SMTP_PORT", 2525))
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
SMTP_PASS    = os.getenv("EMAIL_PASSWORD")
SMTP_USER    = os.getenv("USERNAME")

# -----------------------------------------------
# MODELO
# -----------------------------------------------
class SuscripcionPayload(BaseModel):
    nombre: str
    email: EmailStr

# -----------------------------------------------
# HELPERS
# -----------------------------------------------
def guardar_suscriptor(nombre: str, email: str, conn: ibm_db_dbi.Connection):
    """Inserta el suscriptor en la tabla EMAIL de Db2."""
    cursor = conn.cursor()
    try:
        conn.set_autocommit(False)
        cursor.execute(
            "INSERT INTO EMAIL (NOMBRE, EMAIL) VALUES (?, ?)",
            (nombre, email)
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()


def enviar_bienvenida(nombre: str, email: str):
    """Envía el correo de bienvenida al nuevo suscriptor."""
    subject = "¡Bienvenid@ a la Colmena! 🐝"
    body = f"""\
Hola {nombre},

¡Bienvenid@ a Adentro de la Colmena! 🐝

Estamos muy contentos de tenerte en nuestra comunidad. Aquí es donde
la tecnología, la innovación y las ideas fluyen como la miel.

Pronto recibirás notificaciones sobre:
  • Nuevos episodios del podcast
  • Contenido exclusivo de la comunidad
  • Recursos de tecnología e innovación

Si en algún momento quieres darte de baja, solo responde este correo
y lo haremos de inmediato.

Nos vemos dentro de la colmena,
Ally, Vale y Axel 🐝
"""

    msg = MIMEMultipart()
    msg["From"]    = formataddr((str(Header("Adentro de la Colmena", "utf-8")), EMAIL_SENDER))
    msg["To"]      = email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)


# -----------------------------------------------
# ENDPOINT
# -----------------------------------------------
@app.post("/suscribirse", status_code=status.HTTP_201_CREATED)
async def suscribirse(
    payload: SuscripcionPayload,
    #conn: ibm_db_dbi.Connection = Depends(get_db_connection) conectar a db para subir nuevo subscriptor
):
    """
    Guarda el suscriptor en Db2 y envía un correo de bienvenida.
    """
    #try:
        #guardar_suscriptor(payload.nombre, payload.email, conn)
    #    pass
    #except Exception:
    #    print(traceback.format_exc())
    #    raise HTTPException(
    #        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #        detail="No se pudo guardar la suscripción. Intenta de nuevo."
    #    )

    try:
        enviar_bienvenida(payload.nombre, payload.email)
    except Exception:
        # La suscripción ya fue guardada; solo logueamos el fallo del correo
        print(f"[WARN] No se pudo enviar el correo de bienvenida a {payload.email}")
        print(traceback.format_exc())

    return {
        "status": "ok",
        "message": f"¡Bienvenid@ a la Colmena, {payload.nombre}! Revisa tu correo."
    }
