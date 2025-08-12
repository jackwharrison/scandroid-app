from flask import Flask, render_template, request, send_file, redirect, session, url_for, flash, jsonify, send_from_directory
import requests
from io import BytesIO
from config_loader import load_config, save_config
import json
import os
from config import ADMIN_USERNAME, ADMIN_PASSWORD, FSP_USERNAME, FSP_PASSWORD
from urllib.parse import quote
import subprocess
import zipfile


app = Flask(__name__)
app.secret_key = 'your_secret_key'


translations = {
    "en": {
        "title": "Beneficiary Information",
        "name": "Name",
        "dob": "Date of Birth",
        "photo": "Photo",
        "payment_approved": "Payment Approved",
        "payment_rejected": "Payment Rejected",
        "participant_withdraws": "Participant Withdraws",
        "language": "Language",
        "login": "Login",
        "enter_password": "Enter Password",
        "submit": "Submit",
        "payment_status": "Payment Status",
        "confirm_person": "Confirm this is the correct person",
        "rejection_reason": "Reason for Rejection",
        "already_scanned": "This person has already been scanned and submitted to 121.",
        "success_message": "Payment successfully submitted.",
        "already_submitted_page": "This beneficiary's payment has already been submitted. If you need support, contact support@121.global",
        "config_title": "Configure Fields to Display",
        "field_key": "Field Key (from Kobo)",
        "label_en": "Label (EN)",
        "label_fr": "Label (FR)",
        "label_ar": "Label (AR)",
        "remove": "Remove",
        "add_field": "Add Field",
        "save": "Save",
        "saved_successfully": "Saved successfully",
        "failed_to_save": "Failed to save",
        "logout": "Logout",
        "config_system": "System Configuration",
        "config_display": "Configure Fields to Display",
        "fsp_login": "Login for FSP Admins",
        "fsp_sync_title": "📥 FSP: Sync Offline Records",
        "sync_latest": "Sync Latest Records",
        "syncing": "Syncing...",
        "sync_error": "❌ Failed to sync. Please try again.",
        "sync_initial": "Click sync to see how many beneficiaries are ready for offline validation.",
        "sync_complete": "✅ {count} beneficiaries ready for offline validation.",
        "step1": "Step 1. Sync Latest Records",
        "step2": "Step 2. Import Offline Cache",
        "step3": "Step 3. Scan QR Codes",
        "online": "Online",
        "offline": "Offline",
        "scan_title": "Scan QR",
        "back_to_dashboard": "Back",
        "scan_hint": "Point the camera at the QR code.",
        "start_camera": "Start camera",
        "waiting_to_start": "Waiting to start…",
        "requesting_camera": "Requesting camera… If prompted, tap Allow.",
        "camera_denied": "Camera permission denied or not available.",
        "scanning": "Scanning…",
        "starting_camera": "Starting camera…",
        "footer_dev": "Developed by 510 @ The Netherlands Red Cross"
    },
    "fr": {
        "title": "Informations sur le bénéficiaire",
        "name": "Nom",
        "dob": "Date de naissance",
        "photo": "Photo",
        "payment_approved": "Paiement approuvé",
        "payment_rejected": "Paiement refusé",
        "participant_withdraws": "Le participant se retire",
        "language": "Langue",
        "login": "Connexion",
        "enter_password": "Entrer le mot de passe",
        "submit": "Soumettre",
        "payment_status": "Statut du paiement",
        "confirm_person": "Confirmez que c'est la bonne personne",
        "rejection_reason": "Motif du refus",
        "already_scanned": "Cette personne a déjà été scannée et soumise à 121.",
        "success_message": "Paiement soumis avec succès.",
        "already_submitted_page": "Le paiement de ce bénéficiaire a déjà été soumis. Si vous avez besoin d'aide, contactez support@121.global",
        "config_title": "Configurer les champs à afficher",
        "field_key": "Clé de champ (depuis Kobo)",
        "label_en": "Libellé (EN)",
        "label_fr": "Libellé (FR)",
        "label_ar": "Libellé (AR)",
        "remove": "Supprimer",
        "add_field": "Ajouter un champ",
        "save": "Enregistrer",
        "saved_successfully": "Enregistré avec succès",
        "failed_to_save": "Échec de l'enregistrement",
        "logout": "Déconnexion",
        "config_system": "Configuration du système",
        "config_display": "Configurer les champs à afficher",
        "fsp_login": "Connexion pour les FSP",
        "fsp_sync_title": "📥 FSP : Synchroniser les enregistrements hors ligne",
        "sync_latest": "Synchroniser les derniers enregistrements",
        "syncing": "Synchronisation...",
        "sync_error": "❌ Échec de la synchronisation. Veuillez réessayer.",
        "sync_initial": "Cliquez sur synchroniser pour voir combien de bénéficiaires sont prêts pour la validation hors ligne.",
        "sync_complete": "✅ {count} bénéficiaires prêts pour la validation hors ligne.",
        "step1": "Étape 1. Synchroniser les derniers enregistrements",
        "step2": "Étape 2. Importer le cache hors ligne",
        "step3": "Étape 3. Scanner les codes QR",
        "online": "En ligne",
        "offline": "Hors ligne",
        "scan_title": "Scanner un QR",
        "back_to_dashboard": "Retour",
        "scan_hint": "Pointez la caméra vers le code QR.",
        "start_camera": "Démarrer la caméra",
        "waiting_to_start": "En attente de démarrage…",
        "requesting_camera": "Demande d’accès à la caméra… Si demandé, touchez Autoriser.",
        "camera_denied": "Accès à la caméra refusé ou non disponible.",
        "scanning": "Analyse…",
        "starting_camera": "Démarrage de la caméra…",
        "footer_dev": "Developed by 510 @ The Netherlands Red Cross"        
    },
    "ar": {
        "title": "معلومات المستفيد",
        "name": "الاسم",
        "dob": "تاريخ الميلاد",
        "photo": "صورة",
        "payment_approved": "تمت الموافقة على الدفع",
        "payment_rejected": "تم رفض الدفع",
        "participant_withdraws": "انسحب المستفيد",
        "language": "اللغة",
        "login": "تسجيل الدخول",
        "enter_password": "أدخل كلمة المرور",
        "submit": "إرسال",
        "payment_status": "حالة الدفع",
        "confirm_person": "تأكيد أن هذه هي الشخص الصحيح",
        "rejection_reason": "سبب الرفض",
        "already_scanned": "تم بالفعل مسح هذا الشخص وإرساله إلى 121.",
        "success_message": "تم إرسال الدفع بنجاح.",
        "already_submitted_page": "تم بالفعل إرسال دفعة هذا المستفيد. إذا كنت بحاجة إلى الدعم، فاتصل بـ support@121.global",
        "config_title": "تكوين الحقول المعروضة",
        "field_key": "مفتاح الحقل (من كوبا)",
        "label_en": "التسمية (EN)",
        "label_fr": "التسمية (FR)",
        "label_ar": "التسمية (AR)",
        "remove": "إزالة",
        "add_field": "إضافة حقل",
        "save": "حفظ",
        "saved_successfully": "تم الحفظ بنجاح",
        "failed_to_save": "فشل الحفظ",
        "logout": "تسجيل الخروج",
        "config_system": "إعدادات النظام",
        "config_display": "تكوين الحقول المعروضة",
        "fsp_login": "تسجيل الدخول لمزودي الخدمات المالية",
        "fsp_sync_title": "📥 مزوّد الخدمة: مزامنة السجلات غير المتصلة",
        "sync_latest": "مزامنة أحدث السجلات",
        "syncing": "جارٍ المزامنة...",
        "sync_error": "❌ فشلت عملية المزامنة. يرجى المحاولة مرة أخرى.",
        "sync_initial": "انقر على المزامنة لمعرفة عدد المستفيدين الجاهزين للتحقق دون اتصال.",
        "sync_complete": "✅ {count} مستفيدين جاهزين للتحقق دون اتصال.",
        "step1": "الخطوة 1. مزامنة أحدث السجلات",
        "step2": "الخطوة 2. استيراد ذاكرة التخزين المؤقت دون اتصال",
        "step3": "الخطوة 3. مسح رموز QR",
        "online": "متصل",
        "offline": "غير متصل",
        "scan_title": "مسح رمز QR",
        "back_to_dashboard": "رجوع",
        "scan_hint": "وجّه الكاميرا نحو رمز QR.",
        "start_camera": "بدء تشغيل الكاميرا",
        "waiting_to_start": "بانتظار البدء…",
        "requesting_camera": "جارٍ طلب تشغيل الكاميرا… إذا طُلِب منك ذلك، اضغط سماح.",
        "camera_denied": "تم رفض إذن الكاميرا أو أنها غير متاحة.",
        "scanning": "جارٍ المسح…",
        "starting_camera": "جارٍ بدء تشغيل الكاميرا…",
        "footer_dev": "Developed by 510 @ The Netherlands Red Cross"
    }
}

@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    from config import ADMIN_USERNAME, ADMIN_PASSWORD
    lang = request.args.get("lang", "en")

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for("admin_dashboard", lang=lang))
        else:
            flash("Invalid credentials", "error")

    return render_template("admin_login.html", lang=lang, t=translations.get(lang, translations["en"]))

@app.route("/admin-dashboard")
def admin_dashboard():
    lang = request.args.get("lang", "en")
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login", lang=lang))
    
    return render_template("admin_dashboard.html", lang=lang, t=translations.get(lang, translations["en"]))

@app.route("/admin-logout")
def admin_logout():
    lang = request.args.get("lang", "en")
    session.pop("admin_logged_in", None)
    return redirect(url_for("admin_login", lang=lang))


@app.route("/system-config", methods=["GET", "POST"])
def system_config():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login", lang=request.args.get("lang", "en")))

    lang = request.args.get("lang", "en")
    t = translations.get(lang, translations["en"])

    if request.method == "POST":
        updated_config = {
            "KOBO_TOKEN": request.form.get("KOBO_TOKEN", ""),
            "ASSET_ID": request.form.get("ASSET_ID", ""),
            "PASSWORD": request.form.get("PASSWORD", ""),
            "url121": request.form.get("url121", ""),
            "username121": request.form.get("username121", ""),
            "password121": request.form.get("password121", ""),
            "programId": request.form.get("programId", ""),
            "PAYMENT_ID": request.form.get("PAYMENT_ID", ""),
            "COLUMN_TO_MATCH": request.form.get("COLUMN_TO_MATCH", "")
        }
        save_config(updated_config)
        flash(t["saved_successfully"])
        return redirect(url_for("system_config", lang=lang))

    config = load_config()
    return render_template("system_config.html", config=config, lang=lang, t=t)


@app.route("/config", methods=["GET", "POST"])
def config_page():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login", lang=request.args.get("lang", "en")))

    lang = request.args.get("lang", "en")

    if request.method == "POST":
        config_data = request.get_json()
        try:
            with open("display_config.json", "w", encoding="utf-8") as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    # Handle GET request
    try:
        with open("display_config.json", "r", encoding="utf-8") as f:
            config_data = json.load(f)

        if isinstance(config_data, list):
            config_data = {
                "fields": config_data,
                "photo": {
                    "enabled": True,
                    "labels": {
                        "en": "Photo",
                        "fr": "Photo",
                        "ar": "صورة"
                    }
                }
            }

    except Exception:
        config_data = {
            "fields": [],
            "photo": {
                "enabled": True,
                "labels": {
                    "en": "Photo",
                    "fr": "Photo",
                    "ar": "صورة"
                }
            }
        }

    return render_template(
        "config.html",
        config=config_data,
        lang=lang,
        t=translations.get(lang, translations["en"])
    )


def get_121_token():
    config = load_config()
    payload = {"username": config["username121"], "password": config["password121"]}
    response = requests.post(f"{config['url121']}/api/users/login", json=payload)
    if response.status_code == 201:
        return response.json().get("access_token_general")
    return None

def get_registration_data(reference_id, token):
    config = load_config()
    headers = {'Content-Type': 'application/json'}
    cookies = {'access_token_general': token}
    params = {'referenceId': reference_id}
    url = f"{config['url121']}/api/programs/{config['programId']}/registrations/"
    response = requests.get(url, headers=headers, cookies=cookies, params=params)
    if response.status_code == 200:
        for entry in response.json().get("data", []):
            if entry.get("referenceId") == reference_id:
                return entry
    return None

@app.route("/")
def home():
    return redirect("/login")

@app.route("/login", methods=["GET", "POST"])
def login():
    config = load_config()
    if request.method == "POST":
        password_input = request.form.get("password")
        ben_id = request.form.get("id")
        ben_uuid = request.form.get("uuid")  # NEW
        lang = request.form.get("lang", "en")
        if password_input == config["PASSWORD"]:
            session.clear()
            session.permanent = False
            session['logged_in'] = True
            # Prefer uuid if present
            if ben_uuid:
                return redirect(f"/beneficiary?uuid={ben_uuid}&lang={lang}")
            else:
                return redirect(f"/beneficiary?id={ben_id}&lang={lang}")
        else:
            return render_template("login.html", error="Incorrect password", lang=lang, id=ben_id, t=translations["en"])

    ben_id = request.args.get("id")
    ben_uuid = request.args.get("uuid")  # NEW
    lang = request.args.get("lang", "en")
    return render_template("login.html", error=None, lang=lang, id=ben_id, t=translations.get(lang, translations["en"]))


@app.route("/beneficiary")
def beneficiary():
    config = load_config()
    lang = request.args.get("lang", "en")

    if not session.get("logged_in"):
        # keep both id/uuid in redirect so user returns to correct record
        ben_id = request.args.get("id", "")
        ben_uuid = request.args.get("uuid", "")
        q = f"id={ben_id}" if ben_id else (f"uuid={ben_uuid}" if ben_uuid else "")
        return redirect(f"/login?{q}&lang={lang}" if q else f"/login?lang={lang}")

    ben_id = request.args.get("id")          # Kobo numeric _id (legacy path)
    ben_uuid = request.args.get("uuid")      # Kobo _uuid (new preferred path)

    if not ben_id and not ben_uuid:
        return "Missing beneficiary identifier", 400

    # Load display config (unchanged)
    try:
        with open("display_config.json", "r", encoding="utf-8") as f:
            full_config = json.load(f)
            display_fields = full_config.get("fields", [])
            photo_config = full_config.get("photo", {})
    except Exception:
        display_fields = []
        photo_config = {}

    headers = {"Authorization": f"Token {config['KOBO_TOKEN']}"}

    # If uuid is provided, fetch the record by _uuid first to learn its numeric _id
    if ben_uuid and not ben_id:
        # Query Kobo by _uuid
        params = {
            "format": "json",
            "query": json.dumps({"_uuid": ben_uuid})
        }
        list_url = f"https://kobo.ifrc.org/api/v2/assets/{config['ASSET_ID']}/data/"
        kobo_list = requests.get(list_url, headers=headers, params=params)
        if kobo_list.status_code != 200:
            return "Beneficiary not found.", 404
        payload = kobo_list.json()
        # v2 returns either {"results":[...]} or {"data":[...]} depending on instance; check both
        results = payload.get("results") or payload.get("data") or []
        if not results:
            return "Beneficiary not found.", 404
        data = results[0]
        # Extract numeric _id for photo endpoint & consistency
        ben_id = data.get("_id")
        if not ben_id:
            return "Beneficiary not found.", 404
    else:
        # Legacy: fetch by numeric _id
        rec_url = f"https://kobo.ifrc.org/api/v2/assets/{config['ASSET_ID']}/data/{ben_id}/?format=json"
        kobo_response = requests.get(rec_url, headers=headers)
        if kobo_response.status_code != 200:
            return "Beneficiary not found.", 404
        data = kobo_response.json()
        # Ensure we know the uuid when coming from _id
        ben_uuid = data.get("_uuid")

    # Photo: keep your exact flow (uses numeric id + configurable field name)
    photo_field_name = (photo_config or {}).get("field_name", "photo")
    photo_url = f"/photo/{ben_id}?field={quote(photo_field_name)}"

    # 121 already-submitted check (unchanged)
    token = get_121_token()
    if token and ben_uuid:
        registration_data = get_registration_data(ben_uuid, token)
        if registration_data and registration_data.get("submitted") == "Payment Submitted":
            return redirect(f"/already_submitted?lang={lang}")

    return render_template(
        "beneficiary.html",
        data=data,
        photo_url=photo_url,
        lang=lang,
        t=translations.get(lang, translations["en"]),
        display_fields=display_fields,
        photo_config=photo_config,
        already_submitted=False
    )

@app.route("/photo/<int:ben_id>")
def photo(ben_id):
    config = load_config()
    field_name = request.args.get("field", "photo")  # default to "photo" if not specified

    headers = {"Authorization": f"Token {config['KOBO_TOKEN']}"}
    photo_url = f"https://kobo.ifrc.org/api/v2/assets/{config['ASSET_ID']}/data/{ben_id}/attachments/?xpath={field_name}"
    
    response = requests.get(photo_url, headers=headers)
    if response.status_code == 200:
        return send_file(BytesIO(response.content), mimetype='image/jpeg')
    else:
        return "Photo not found", 404

@app.route("/success")
def success():
    lang = request.args.get("lang", "en")
    return render_template("success.html", lang=lang, t=translations.get(lang, translations["en"]))

@app.route("/logout")
def logout():
    lang = request.args.get("lang", "en")
    session.clear()
    return redirect(url_for("login", lang=lang))

@app.route("/already_submitted")
def already_submitted():
    lang = request.args.get("lang", "en")
    return render_template("already_submitted.html", lang=lang, t=translations.get(lang, translations["en"]))

@app.route("/update_status", methods=["POST"])
def update_status():
    import csv
    import io
    from datetime import datetime
    import os

    config = load_config()
    ben_id = request.form.get("id")
    status = request.form.get("status")
    rejection_reason = request.form.get("rejection_reason", "")
    lang = request.form.get("lang", "en")

    column_to_match = config.get("COLUMN_TO_MATCH", "phoneNumber")
    payment_id = config.get("PAYMENT_ID")
    program_id = config.get("programId")

    if not payment_id or not program_id:
        flash("Missing Payment ID or Program ID in system config", "error")
        return redirect(f"/beneficiary?id={ben_id}&lang={lang}")

    # Step 1: Get Kobo UUID
    headers = {"Authorization": f"Token {config['KOBO_TOKEN']}"}
    kobo_resp = requests.get(
        f"https://kobo.ifrc.org/api/v2/assets/{config['ASSET_ID']}/data/{ben_id}/?format=json", 
        headers=headers
    )
    if kobo_resp.status_code != 200:
        flash("Could not retrieve data from Kobo", "error")
        return redirect(f"/beneficiary?id={ben_id}&lang={lang}")

    kobo_data = kobo_resp.json()
    uuid = kobo_data.get("_uuid")
    if not uuid:
        flash("UUID not found in Kobo record", "error")
        return redirect(f"/beneficiary?id={ben_id}&lang={lang}")

    # Step 2: Get payment transactions
    token = get_121_token()
    if not token:
        flash("Login to 121 failed", "error")
        return redirect(f"/beneficiary?id={ben_id}&lang={lang}")

    tx_url = f"{config['url121']}/api/programs/{program_id}/payments/{payment_id}/transactions"
    tx_resp = requests.get(tx_url, cookies={"access_token_general": token})
    if tx_resp.status_code != 200:
        flash(f"Failed to fetch transactions: {tx_resp.text}", "error")
        return redirect(f"/beneficiary?id={ben_id}&lang={lang}")

    transactions = tx_resp.json()
    tx = next((t for t in transactions if t.get("registrationReferenceId") == uuid), None)
    if not tx:
        flash("No transaction found for this beneficiary in the payment", "error")
        return redirect(f"/beneficiary?id={ben_id}&lang={lang}")

    registration_id = tx.get("registrationId")
    if not registration_id:
        flash("No registrationId found in matching transaction", "error")
        return redirect(f"/beneficiary?id={ben_id}&lang={lang}")

    # Step 3: Get full registration using ID (numeric)
    reg_url = f"{config['url121']}/api/programs/{program_id}/registrations/{registration_id}"
    reg_resp = requests.get(reg_url, cookies={"access_token_general": token})
    if reg_resp.status_code != 200:
        flash(f"Could not fetch registration details: {reg_resp.text}", "error")
        return redirect(f"/beneficiary?id={ben_id}&lang={lang}")

    registration = reg_resp.json()
    match_value = registration.get(column_to_match)
    if not match_value:
        flash(f"Field '{column_to_match}' not found in registration", "error")
        return redirect(f"/beneficiary?id={ben_id}&lang={lang}")

    # Step 4: Build reconciliation CSV
    status_value = "success" if status == "Payment Approved" else "error"
    csv_buffer = io.StringIO()
    writer = csv.DictWriter(csv_buffer, fieldnames=[column_to_match, "status"])
    writer.writeheader()
    writer.writerow({column_to_match: match_value, "status": status_value})

    # Step 5: Upload to reconciliation endpoint
    upload_url = f"{config['url121']}/api/programs/{program_id}/payments/{payment_id}/excel-reconciliation"
    files = {"file": ("reconciliation.csv", csv_buffer.getvalue(), "text/csv")}
    upload_resp = requests.post(upload_url, files=files, cookies={"access_token_general": token})

    # Step 6: Log result
    log_row = {
        "timestamp": datetime.utcnow().isoformat(),
        "beneficiary_id": ben_id,
        "uuid": uuid,
        "match_column": column_to_match,
        "match_value": match_value,
        "status": status,
        "rejection_reason": rejection_reason,
        "success": upload_resp.status_code == 201
    }

    log_exists = os.path.exists("reconciliation_log.csv")
    with open("reconciliation_log.csv", "a", newline='', encoding="utf-8") as log_file:
        writer = csv.DictWriter(log_file, fieldnames=log_row.keys())
        if not log_exists:
            writer.writeheader()
        writer.writerow(log_row)

    if upload_resp.status_code == 201:
        return redirect(f"/success?lang={lang}")
    else:
        flash(f"Reconciliation upload failed: {upload_resp.text}", "error")
        return redirect(f"/beneficiary?id={ben_id}&lang={lang}")

@app.route("/fsp-login", methods=["GET", "POST"])
def fsp_login():
    error = None
    lang = request.args.get("lang", "en")

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == FSP_USERNAME and password == FSP_PASSWORD:
            session["fsp_logged_in"] = True
            return redirect(url_for("fsp_admin", lang=lang))
        else:
            error = "Invalid credentials"

    return render_template("fsp_login.html", lang=lang, error=error)


@app.route("/fsp-admin")
def fsp_admin():
    if not session.get("fsp_logged_in"):
        return redirect(url_for("fsp_login"))

    lang = request.args.get("lang", "en")
    t = translations.get(lang, translations["en"])
    return render_template("fsp_admin.html", lang=lang, t=t)


@app.route("/sync-fsp")
def sync_fsp():
    import subprocess

    try:
        result = subprocess.run(
            ["python", "offline_sync.py"],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        output = result.stdout.strip()
        error_output = result.stderr.strip()

        if result.returncode != 0:
            return jsonify({
                "success": False,
                "message": f"❌ Script failed with error:\n{error_output or output}"
            })

        # Look for any line that mentions 'beneficiaries'
        for line in output.splitlines():
            if "beneficiaries" in line.lower():
                return jsonify({"success": True, "message": f"✅ {line.strip()}"})

        return jsonify({
            "success": True,
            "message": "✅ Sync completed, but no beneficiaries were found."
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"❌ Error running sync: {str(e)}"
        })
@app.route("/fsp-logout")
def fsp_logout():
    session.pop("fsp_logged_in", None)
    return redirect(url_for("fsp_login"))


@app.route("/scan")
def scan():
    # Only FSP-logged-in users should scan
    lang = request.args.get("lang", "en")
    if not session.get("fsp_logged_in"):
        return redirect(url_for("fsp_login", lang=lang))
    return render_template("scan.html", lang=lang, t=translations.get(lang, translations["en"]))


@app.route('/service-worker.js')
def sw():
    return send_from_directory('static', 'service-worker.js', mimetype='application/javascript')

@app.route('/manifest.webmanifest')
def manifest():
    return send_from_directory('static', 'manifest.webmanifest', mimetype='application/manifest+json')

@app.route('/offline')
def offline():
    return render_template('offline.html')


from io import BytesIO

@app.route("/api/offline/latest.zip")
def api_offline_latest_zip():
    base_dir = "offline-cache"
    if not os.path.isdir(base_dir):
        return jsonify({"error": "No offline cache found"}), 404

    # Find latest batch directory by modified time
    batch_dirs = [
        os.path.join(base_dir, d)
        for d in os.listdir(base_dir)
        if os.path.isdir(os.path.join(base_dir, d))
    ]
    if not batch_dirs:
        return jsonify({"error": "No batches found"}), 404

    latest = max(batch_dirs, key=os.path.getmtime)

    # Zip the latest batch in memory
    mem = BytesIO()
    with zipfile.ZipFile(mem, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(latest):
            for fname in files:
                full_path = os.path.join(root, fname)
                arcname = os.path.relpath(full_path, latest)  # keep paths relative to batch root
                zf.write(full_path, arcname)
    mem.seek(0)

    return send_file(
        mem,
        mimetype="application/zip",
        as_attachment=True,
        download_name="latest_offline_cache.zip",
    )

@app.route("/ping")
def ping():
    return ("", 204)


@app.route("/beneficiary-offline")
def beneficiary_offline():
    # expected: /beneficiary-offline?uuid=<registrationReferenceId>&lang=en
    uuid = request.args.get("uuid")
    lang = request.args.get("lang", "en")

    # CHANGE: don't return 400; render a shell so the SW can precache a 200
    if not uuid:
        uuid = ""

    # load display config (same file you already use)
    try:
        with open("display_config.json", "r", encoding="utf-8") as f:
            full_config = json.load(f)
            display_fields = full_config.get("fields", [])
            photo_config = full_config.get("photo", {})
    except Exception:
        display_fields = []
        photo_config = {}

    # pass Fernet key for client-side decrypt when we add it
    config = load_config()
    enc_key = config.get("ENCRYPTION_KEY", "")

    return render_template(
        "beneficiary_offline.html",
        uuid=uuid,  # may be "", the page will prefer URL ?uuid=...
        lang=lang,
        t=translations.get(lang, translations["en"]),
        display_fields=display_fields,
        photo_config=photo_config,
        fernet_key=enc_key,
    )

@app.route("/success-offline")
def success_offline():
    lang = request.args.get("lang", "en")
    return render_template("success_offline.html", lang=lang)

@app.route("/system-config.json")
def system_config_json():
    config = load_config()
    return jsonify({
        "COLUMN_TO_MATCH": config.get("COLUMN_TO_MATCH", "phoneNumber")
    })


@app.route("/version.json")
def version_json():
    return jsonify({"version": "4"})


@app.route("/force-reset")
def force_reset():
    return """
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>Force Reset</title>
      <style>
        body { font-family: sans-serif; padding: 2em; text-align: center; }
        button { padding: 1em 2em; font-size: 1.2em; background: #c8102e; color: white; border: none; border-radius: 6px; cursor: pointer; }
      </style>
    </head>
    <body>
      <h1>🔄 Force Reset</h1>
      <p>This will:</p>
      <ul style="text-align: left; display: inline-block;">
        <li>🧹 Clear saved beneficiary data</li>
        <li>🔌 Unregister the service worker</li>
        <li>🔁 Reload the latest version of the app</li>
      </ul>
      <br>
      <button onclick="clearAll()">Reset App</button>
      <script>
        async function clearAll() {
          try {
            // Delete IndexedDB databases
            if ('databases' in indexedDB) {
              const dbs = await indexedDB.databases();
              for (const db of dbs) {
                if (db.name) indexedDB.deleteDatabase(db.name);
              }
            } else {
              indexedDB.deleteDatabase("beneficiaries"); // fallback for older browsers
              indexedDB.deleteDatabase("offlineActions");
            }

            // Unregister all service workers
            const regs = await navigator.serviceWorker.getRegistrations();
            for (const reg of regs) await reg.unregister();

            alert("✅ App data cleared. Reloading fresh.");
            location.href = "/";
          } catch (e) {
            alert("⚠️ Failed to reset: " + e.message);
          }
        }
      </script>
    </body>
    </html>
    """
