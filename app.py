import os
import requests
from flask import Flask, request, jsonify
import telebot
from telebot import types
import firebase_admin
from firebase_admin import db

# Firebase نى ئاددىي شەكىلدە ئېچىش
if not firebase_admin._apps:
    firebase_admin.initialize_app(options={
        'databaseURL': 'https://koznak-store-default-rtdb.firebaseio.com/'
    })

app = Flask(__name__)

# سىزنىڭ تېلېگرامما بوت Token
BOT_TOKEN = "8811660953:AAFqjQ3Zmpc9bcppIW1rP8v6Ly2fCvgNRVQ"
bot = telebot.TeleBot(BOT_TOKEN)

# تېلېگراممىدا ئاگادارلىق كېلىدىغان Admin نىڭ Chat ID (أو نۇمۇرىڭىز)
ADMIN_CHAT_ID = "8811660953"

@app.route('/api/verify', methods=['POST'])
def verify_receipt():
    image = request.files.get('image')
    expected_amount = request.form.get('expected_amount')
    username = request.form.get('username', 'مېھمان')
    tx_id = request.form.get('tx_id', 'نومۇرسىز')
    deposit_id = request.form.get('deposit_id', 'dep_' + str(int(os.urandom(4).hex(), 16)))

    if not image:
        return jsonify({"status": "error", "message": "رەسىم تېپىلمىدى"})

    img_path = f"/tmp/{image.filename}"
    image.save(img_path)

    try:
        markup = types.InlineKeyboardMarkup()
        btn_approve = types.InlineKeyboardButton("✅ قوبۇللاش (+قوشۇش)", callback_data=f"app_{deposit_id}_{username}_{expected_amount}")
        btn_reject = types.InlineKeyboardButton("❌ رەت قىلىش", callback_data=f"rej_{deposit_id}_{username}")
        markup.add(btn_approve, btn_reject)

        caption = (
            f"💰 **يېڭى شامكەش پۇل قاچىلاش ئىلتىماسى!**\n\n"
            f"👤 ئابونت: `{username}`\n"
            f"💵 سومما: `{expected_amount} شامكەش`\n"
            f"🧾 تالون No: `{tx_id}`\n\n"
            f"👇 تۆۋەندىكى كۇنۇپكىنى بېسىپ تەستىقلاڭ:"
        )

        with open(img_path, 'rb') as photo:
            bot.send_photo(ADMIN_CHAT_ID, photo, caption=caption, parse_mode="Markdown", reply_markup=markup)
            
    except Exception as e:
        print("Telegram error:", e)

    return jsonify({
        "status": "success",
        "data": {
            "is_valid_receipt": True,
            "is_matching": True,
            "reason": "ئىلتىماس تېلېگرامما بوتىغا ئەۋەتىلدى، باشقۇرغۇچى تەستىقلايدۇ."
        }
    })

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    data = call.data
    if data.startswith("app_"):
        _, dep_id, username, amount = data.split("_")
        amount = float(amount)
        
        # Firebase دە ئابونتقا پۇل قوشۇش
        ref = db.reference(f'users/{username}/balance')
        current_bal = ref.get() or 0
        ref.set(current_bal + amount)
        
        db.reference(f'deposit_requests/{dep_id}/status').set('approved')

        bot.answer_callback_query(call.id, "مۇۋەپپەقىيەتلىك تەستىقلاندى!")
        bot.edit_message_caption(
            chat_id=call.message.chat.id, 
            message_id=call.message.message_id, 
            caption=f"✅ **تەستىقلاندى ۋە پۇل قوشۇلدى!**\n\n👤 ئابونت: {username}\n💵 قوشۇلغىنى: +{amount} شامكەش",
            parse_mode="Markdown"
        )
        
    elif data.startswith("rej_"):
        _, dep_id, username = data.split("_")
        db.reference(f'deposit_requests/{dep_id}/status').set('rejected')

        bot.answer_callback_query(call.id, "تەلەپ رەت قىلىندى!")
        bot.edit_message_caption(
            chat_id=call.message.chat.id, 
            message_id=call.message.message_id, 
            caption=f"❌ **بۇ تەلەپ رەت قىلىندى.**\n\n👤 ئابونت: {username}",
            parse_mode="Markdown"
        )

if __name__ == '__main__':
    import threading
    threading.Thread(target=bot.infinity_polling, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
