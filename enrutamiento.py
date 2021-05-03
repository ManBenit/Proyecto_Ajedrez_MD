import os
from netmiko import ConnectHandler;

#variables globales
user_name="admin";
password="admin01";
secret="1234";




def get_neighbour(neighbour):
    elementos=neighbour.split(" ");
    return {
        "hostname": elementos[1][0:2],
        "ip_vecino_inmediato":elementos[6],
        "nombre_interfaz":elementos[8]
    }

def comando_neighbors(respuesta_neighbor):
    primer_particion=respuesta_neighbor.replace("\n"," ").replace(",","").strip().split("Device ID:");
    primer_particion.pop(0);
    lista=[];
    for neighbour in primer_particion:
        neighbour_json=get_neighbour(neighbour);
        lista.append(neighbour_json);

    return  lista;


def get_networkmask(prefix):

    prefix_int=int(prefix);
    cadena="";
    ipv4len=32;
    ceros=32-prefix_int;

    for i in range(0,int(prefix_int)):
        cadena=cadena+"1";

    for i in range(0,ceros):
        cadena=cadena+"0";

    primer_octeto=cadena[0:8];
    segundo_octeto=cadena[8:16];
    tercer_octeto=cadena[16:24];
    cuarto_octeto=cadena[24:]

    return str(int(primer_octeto, 2))+"."+str(int(segundo_octeto, 2))+"."+str(int(tercer_octeto, 2))+"."+str(int(cuarto_octeto, 2))



def show_ip_row(resultado):

    resultado=resultado.strip().replace("\n","").split(" ");
    #print(resultado);
    id_red=resultado[3].split("/")[0];
    prefix=resultado[3].split("/")[1];

    return {
        "id_red":id_red,
        "prefix":prefix,
        "networkmask": get_networkmask(prefix)
    }

#*****************configurar_enrutamiento_estatico (SIN COMUNICACION CON EL neighbour)

def enrutatamiento_estatisco(mi_ip,siguiente_salto,idRed):

    conf_commands=["ip route "+idRed+" 255.255.255.0 "+siguiente_salto];
    snd_commandos=netmiko_connection(mi_ip,conf_commands,True);
    return  snd_commandos;

def enrutamiento_ospf(mi_ip,siguiente_salto):
    informacion_red = netmiko_connection(mi_ip,"show ip route " +siguiente_salto,False);
    get_neighbour_information = show_ip_row(informacion_red);


    comandos = ["interface loopback 0",
                "ip add 200.0.0.3 255.255.255.255"]
    ejecucion=netmiko_connection(mi_ip,comandos,True);

    comando="network "+get_neighbour_information["id_red"]+" 0.0.0.255 area 0";

    comandos=["router ospf 1",
              "redistribute rip subnets",
              "redistribute static subnets",
              comando]
    ejecucion=netmiko_connection(mi_ip,comandos,True);
    return ejecucion;

def enrutamiento_rip(mi_ip, siguiente_salto):
    informacion_red = netmiko_connection(mi_ip, "show ip route " + siguiente_salto);
    get_neighbour_information = show_ip_row(informacion_red);

    comando = "network " + get_neighbour_information["id_red"];

    comandos = ["router rip",
                "version 2",
                "redistribute ospf 1 match internal external 1 external 2",
                "redistribute static",
                "no auto-summary",
                "default-information originate",
                comando]

    ejecucion = netmiko_connection(mi_ip, comandos,True);

    return ejecucion



def netmiko_connection(ip_vecino_inmediato,comando, isForConfig=False):
    cisco1 = {
        "device_type": "cisco_ios",
        "ip": ip_vecino_inmediato,
        "username": user_name,
        "password": password,
        "secret": secret
    }
    net_connect = ConnectHandler(**cisco1)
    net_connect.enable()
    if(isForConfig):
        salidaComando = net_connect.send_config_set(comando);
    else:
        salidaComando = net_connect.send_command(comando);

    net_connect.disconnect()
    return  salidaComando;


if __name__ == "__main__":
    informacion_interfaz_enlace = os.popen('ip route').read()
    informacion_array=informacion_interfaz_enlace.strip().replace("\n","").split(" ");
    interfaz={
    		       "VMGateway":informacion_array[2],
    		       "prefix":informacion_array[9].split("/")[1],
    		       "ip":informacion_array[9].split("/")[0]
    		    }

    comando_neighbours = netmiko_connection(interfaz["VMGateway"],"show cdp neighbors detail | i Device ID|IP address|Interface:")

    # obtenemos los neighbours del router
    lista_neighbours = comando_neighbors(comando_neighbours);

    contador=0;
    #Enrutamiento estático
    while(contador<len(lista_neighbours)):
        neighbour=lista_neighbours[contador];
        print("Configurando enrutanmiento estatico para:",neighbour["hostname"] )
        ips={
            "R1":"10.0.5.0",
            "R2" :"10.0.6.0",
            "R3":"10.0.7.0"
        }
        j = enrutatamiento_estatisco(interfaz["VMGateway"], neighbour["ip_vecino_inmediato"],ips[neighbour["hostname"]]);
        contador=contador+1;
    #Enrutamiento rip y ospf
    for neighbour in lista_neighbours:

        if (neighbour["hostname"] == "R2"):
            enrutamiento_rip(interfaz["VMGateway"], neighbour["ip_vecino_inmediato"]);
            print("Listo enrutamiento RIP:",neighbour["hostname"])
        else:
            if (neighbour["hostname"] == "R3"):
                enrutamiento_ospf(interfaz["VMGateway"], neighbour["ip_vecino_inmediato"])
                print("Listo enrutamiento RIP:", neighbour["hostname"])

