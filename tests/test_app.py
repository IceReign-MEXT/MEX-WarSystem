import os
os.environ["DATABASE_URL"]="sqlite://"
os.environ["SECRET_KEY"]="test-secret"
os.environ["COOKIE_SECURE"]="false"
import app as service

def setup_function():
    with service.app.app_context():
        service.db.drop_all()
        service.db.create_all()

def test_health_endpoint():
    response=service.app.test_client().get("/health")
    assert response.status_code==200
    assert response.json["status"]=="ok"

def test_home_page_renders():
    response=service.app.test_client().get("/")
    assert response.status_code==200
    assert b"MEX WAR SYSTEM" in response.data

def test_add_valid_ethereum_watch():
    response=service.app.test_client().post("/watch",data={"chain":"eth","address":"0x"+"a"*40,"label":"Test wallet"})
    assert response.status_code==302
    with service.app.app_context():
        assert service.Watch.query.count()==1

def test_reject_invalid_ethereum_watch():
    response=service.app.test_client().post("/watch",data={"chain":"eth","address":"not-an-address"})
    assert response.status_code==302
    with service.app.app_context():
        assert service.Watch.query.count()==0
