import os,hmac,hashlib,secrets,logging
from datetime import datetime,timedelta
import requests
from flask import Flask,request,jsonify,render_template,redirect,url_for,flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.middleware.proxy_fix import ProxyFix

logging.basicConfig(level=os.getenv("LOG_LEVEL","INFO"))
log=logging.getLogger("mexwar")
app=Flask(__name__)
app.wsgi_app=ProxyFix(app.wsgi_app,x_for=1,x_proto=1)
app.config.update(SECRET_KEY=os.getenv("SECRET_KEY","dev-only-change-this"),SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL","sqlite:///mexwar.db").replace("postgres://","postgresql://",1),SQLALCHEMY_TRACK_MODIFICATIONS=False,SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SAMESITE="Lax",SESSION_COOKIE_SECURE=os.getenv("COOKIE_SECURE","true").lower()=="true")
db=SQLAlchemy(app)
class Watch(db.Model):
 id=db.Column(db.Integer,primary_key=True); address=db.Column(db.String(120),nullable=False,index=True); chain=db.Column(db.String(12),nullable=False); label=db.Column(db.String(80),default="My wallet"); created_at=db.Column(db.DateTime,default=datetime.utcnow)
class Customer(db.Model):
 id=db.Column(db.Integer,primary_key=True); email=db.Column(db.String(254),unique=True,nullable=False,index=True); plan=db.Column(db.String(24),default="free"); status=db.Column(db.String(20),default="inactive"); expires_at=db.Column(db.DateTime); paystack_reference=db.Column(db.String(100),unique=True); created_at=db.Column(db.DateTime,default=datetime.utcnow)
PLANS={"starter":("Starter","PLAN_STARTER_NGN"),"pro":("Pro","PLAN_PRO_NGN"),"team":("Team","PLAN_TEAM_NGN")}
def price(plan):
 try:return max(0,int(os.getenv(PLANS[plan][1],"0")))
 except:return 0
@app.after_request
def headers(r):
 r.headers["X-Content-Type-Options"]="nosniff";r.headers["X-Frame-Options"]="DENY";r.headers["Referrer-Policy"]="strict-origin-when-cross-origin";return r
@app.get("/health")
def health():
 try:db.session.execute(db.text("SELECT 1"))
 except Exception:return jsonify(status="degraded",database="unavailable"),503
 return jsonify(status="ok",service="MEX WAR SYSTEM",database="ok")
@app.get("/")
def home():
 return render_template("index.html",watches=Watch.query.order_by(Watch.created_at.desc()).limit(20).all(),plans=PLANS,prices={p:price(p) for p in PLANS},paystack_ready=bool(os.getenv("PAYSTACK_SECRET_KEY")),support=os.getenv("SUPPORT_URL","mailto:support@icereignsystems.com"))
@app.post("/watch")
def add_watch():
 chain=(request.form.get("chain") or "").lower();addr=(request.form.get("address") or "").strip();label=(request.form.get("label") or "My wallet").strip()[:80]
 if chain not in ("sol","eth") or not addr or len(addr)>120:flash("Enter a supported chain and public address.","error");return redirect(url_for("home"))
 if chain=="eth" and not(addr.startswith("0x") and len(addr)==42):flash("Ethereum address format is invalid.","error");return redirect(url_for("home"))
 if chain=="sol" and not(32<=len(addr)<=44):flash("Solana address length is invalid.","error");return redirect(url_for("home"))
 if not Watch.query.filter_by(chain=chain,address=addr).first():db.session.add(Watch(chain=chain,address=addr,label=label));db.session.commit();flash("Public wallet added to watchlist.","success")
 else:flash("Wallet is already on the watchlist.","info")
 return redirect(url_for("home"))
@app.get("/api/token/<path:q>")
def token(q):
 if len(q)>100:return jsonify(error="Query too long"),400
 try:
  r=requests.get("https://api.dexscreener.com/latest/dex/search/",params={"q":q},timeout=12);r.raise_for_status()
  rows=[]
  for p in (r.json().get("pairs") or [])[:12]:
   rows.append({"chain":p.get("chainId"),"base":(p.get("baseToken") or {}).get("symbol"),"priceUsd":p.get("priceUsd"),"liquidityUsd":(p.get("liquidity") or {}).get("usd"),"volume24h":(p.get("volume") or {}).get("h24"),"url":p.get("url")})
  return jsonify(results=rows,source="DexScreener",notice="Informational market data; not a safety certification.")
 except requests.RequestException:log.exception("DexScreener unavailable");return jsonify(error="Market data temporarily unavailable"),502
@app.post("/checkout")
def checkout():
 secret=os.getenv("PAYSTACK_SECRET_KEY","");email=(request.form.get("email") or "").strip().lower();plan=request.form.get("plan","");amt=price(plan) if plan in PLANS else 0
 base=os.getenv("APP_BASE_URL","").rstrip("/")
 if not secret or not base.startswith("https://"):flash("Secure checkout is not configured yet. Contact support.","info");return redirect(url_for("home"))
 if "@" not in email or amt<100:flash("Valid email and configured plan are required.","error");return redirect(url_for("home"))
 ref="MEX-"+secrets.token_urlsafe(18)
 try:
  r=requests.post("https://api.paystack.co/transaction/initialize",json={"email":email,"amount":amt*100,"reference":ref,"callback_url":base+"/payment/verify","metadata":{"product":"MEX WAR SYSTEM","plan":plan}},headers={"Authorization":"Bearer "+secret},timeout=15);d=r.json()
  if not r.ok or not d.get("status"):raise ValueError(d.get("message","Payment initialization failed"))
  c=Customer.query.filter_by(email=email).first() or Customer(email=email);c.plan=plan;c.status="pending";c.paystack_reference=ref;db.session.add(c);db.session.commit();return redirect(d["data"]["authorization_url"],code=303)
 except Exception:db.session.rollback();log.exception("Checkout init failed");flash("Checkout could not start. Retry or contact support.","error");return redirect(url_for("home"))
def verify(ref):
 c=Customer.query.filter_by(paystack_reference=ref).first()
 if not c:return False
 r=requests.get("https://api.paystack.co/transaction/verify/"+ref,headers={"Authorization":"Bearer "+os.getenv("PAYSTACK_SECRET_KEY","")},timeout=15);d=r.json().get("data") or {}
 if not r.ok or d.get("status")!="success" or d.get("amount")!=price(c.plan)*100 or (d.get("customer") or {}).get("email","").lower()!=c.email:return False
 c.status="active";now=datetime.utcnow();c.expires_at=max(c.expires_at or now,now)+timedelta(days=30);db.session.commit();return True
@app.get("/payment/verify")
def payment_verify():
 try:ok=verify(request.args.get("reference",""));flash("Payment verified; subscription activated." if ok else "Payment not confirmed. Do not pay again; contact support with your reference.","success" if ok else "info")
 except Exception:db.session.rollback();log.exception("Payment verify failed");flash("Verification temporarily unavailable. Contact support.","error")
 return redirect(url_for("home"))
@app.post("/webhooks/paystack")
def webhook():
 secret=os.getenv("PAYSTACK_SECRET_KEY","");sig=request.headers.get("x-paystack-signature","");raw=request.get_data();digest=hmac.new(secret.encode(),raw,hashlib.sha512).hexdigest()
 if not secret or not hmac.compare_digest(sig,digest):return "invalid signature",401
 event=request.get_json(silent=True) or {}
 if event.get("event")=="charge.success":
  try:verify((event.get("data") or {}).get("reference",""))
  except Exception:db.session.rollback();log.exception("Webhook failed");return "retry",500
 return jsonify(received=True)
@app.errorhandler(404)
def missing(_):return render_template("error.html",code=404,message="That page does not exist."),404
@app.errorhandler(500)
def failure(_):db.session.rollback();return render_template("error.html",code=500,message="Something went wrong. Try again."),500
with app.app_context():db.create_all()
if __name__=="__main__":app.run(host="0.0.0.0",port=int(os.getenv("PORT","10000")))
