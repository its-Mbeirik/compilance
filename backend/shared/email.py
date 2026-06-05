"""
Email sending via SMTP.
Configure via environment variables:
  SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM, APP_URL
If SMTP_HOST or SMTP_USER is empty, emails are logged but not sent (dev mode).
"""
import logging
import os
import smtplib
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)

APP_URL = os.getenv("APP_URL", "http://localhost:3000")


def _smtp_config() -> dict:
    """Read SMTP config fresh at call time to avoid module-level caching issues."""
    return {
        "host": os.getenv("SMTP_HOST", ""),
        "port": int(os.getenv("SMTP_PORT", "587")),
        "user": os.getenv("SMTP_USER", ""),
        "pwd":  os.getenv("SMTP_PASSWORD", ""),
        "frm":  os.getenv("SMTP_FROM", "noreply@conformia.mr"),
    }


def send_email(to: str, subject: str, html: str) -> None:
    cfg = _smtp_config()
    if not cfg["host"] or not cfg["user"]:
        print(f"[EMAIL] SMTP non configuré — email ignoré ({to})", flush=True)
        return
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = cfg["frm"]
        msg["To"]      = to
        msg.attach(MIMEText(html, "html", "utf-8"))
        with smtplib.SMTP(cfg["host"], cfg["port"], timeout=20) as srv:
            srv.ehlo()
            srv.starttls()
            srv.ehlo()
            srv.login(cfg["user"], cfg["pwd"])
            srv.sendmail(cfg["frm"], to, msg.as_string())
        print(f"[EMAIL] ✓ Envoyé à {to}", flush=True)
    except Exception as exc:
        print(f"[EMAIL] ✗ Erreur SMTP pour {to}: {exc}", flush=True)


def _send_in_thread(fn, *args) -> None:
    """Run fn(*args) in a daemon thread so SMTP never blocks the HTTP response."""
    def _run():
        try:
            fn(*args)
        except Exception as exc:
            logger.error("Erreur thread email : %s", exc, exc_info=True)
    t = threading.Thread(target=_run, daemon=True)
    t.start()


# ── Email templates ────────────────────────────────────────────────────────────

def _base(title: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#f5f5f5;font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr><td align="center" style="padding:40px 16px;">
      <table width="600" cellpadding="0" cellspacing="0"
             style="background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,.08);">
        <tr>
          <td style="background:#111;padding:24px 32px;">
            <span style="color:#fff;font-size:20px;font-weight:700;">⚖ ConformIA</span>
          </td>
        </tr>
        <tr>
          <td style="padding:32px;">
            <h2 style="margin:0 0 16px;color:#111;font-size:20px;">{title}</h2>
            {body}
          </td>
        </tr>
        <tr>
          <td style="padding:16px 32px;background:#f9f9f9;color:#999;font-size:12px;">
            ConformIA — Assistant de conformité contractuelle mauritanien
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body></html>"""


def send_verification_email(to: str, name: str, token: str) -> None:
    app_url = os.getenv("APP_URL", "http://localhost:3000")
    link = f"{app_url}/verify-email?token={token}"
    body = f"""
      <p style="color:#444;line-height:1.6;">Bonjour <strong>{name}</strong>,</p>
      <p style="color:#444;line-height:1.6;">
        Merci de vous être inscrit sur ConformIA. Cliquez sur le bouton ci-dessous
        pour vérifier votre adresse email. Votre compte sera ensuite examiné par un administrateur.
      </p>
      <p style="margin:24px 0;">
        <a href="{link}"
           style="background:#111;color:#fff;padding:12px 28px;text-decoration:none;
                  border-radius:8px;font-weight:600;font-size:14px;">
          Vérifier mon adresse email
        </a>
      </p>
      <p style="color:#999;font-size:12px;">
        Ce lien est valable <strong>24 heures</strong>.
        Si vous n'avez pas créé de compte, ignorez cet email.
      </p>
    """
    _send_in_thread(send_email, to, "ConformIA — Vérifiez votre adresse email",
                    _base("Vérification de votre email", body))


def send_reset_email(to: str, name: str, token: str) -> None:
    app_url = os.getenv("APP_URL", "http://localhost:3000")
    link = f"{app_url}/reset-password?token={token}"
    body = f"""
      <p style="color:#444;line-height:1.6;">Bonjour <strong>{name}</strong>,</p>
      <p style="color:#444;line-height:1.6;">
        Vous avez demandé la réinitialisation de votre mot de passe ConformIA.
        Cliquez sur le bouton ci-dessous pour choisir un nouveau mot de passe.
      </p>
      <p style="margin:24px 0;">
        <a href="{link}"
           style="background:#111;color:#fff;padding:12px 28px;text-decoration:none;
                  border-radius:8px;font-weight:600;font-size:14px;">
          Réinitialiser mon mot de passe
        </a>
      </p>
      <p style="color:#999;font-size:12px;">
        Ce lien est valable <strong>1 heure</strong>.
        Si vous n'avez pas fait cette demande, ignorez cet email — votre mot de passe ne changera pas.
      </p>
    """
    _send_in_thread(send_email, to, "ConformIA — Réinitialisation de mot de passe",
                    _base("Réinitialisation de mot de passe", body))
