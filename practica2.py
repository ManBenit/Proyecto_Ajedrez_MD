from flask import Flask
from flask.templating import render_template
from netmiko import ConnectHandler
app = Flask(__name__)

def conectarRouter(): #ip, puerto, usuario, contra
    """router= {
        "device_type": "cisco_ios_telnet",
        "ip": str(ip),
        "port": str(puerto),
        "username": str(usuario),
        "password": str(contra)
    }"""
    router= {
        "device_type": "cisco_ios",
        "ip": "192.168.0.1",
        "port": "22",
        "secret": "1234",
        "username": "admin",
        "password": "admin01"
    }
    return router

def resetPrompt(net_connect):
    if net_connect.ckeck_enable_mode():
        net_connect.exit_enable_mode()
    if net_connect.ckeck_config_mode():
        net_connect.exit_config_mode()
    

@app.route("/")
def menuPrincipal():
    return render_template("index.html")

@app.route("/creacion/")
def crearUsuario():
    router= ConnectHandler(**conectarRouter())
    prompt= router.find_prompt()
    print(prompt)
    resetPrompt(router)
    prompt= router.find_prompt()
    print(prompt)
    result= router.send_command("sh ip int br")
    print(result)
    return "Crear usuario"

@app.route("/baja/")
def bajaUsuario():
    return "Dar de baja un usuario"

@app.route("/modificacion/")
def elimUsuario():
    return "Modificación de usuario"

if __name__ == '__main__':
    app.run(port=3000, debug=True)