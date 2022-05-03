from flask import Flask, request, jsonify
from flask_cors import CORS
import xml.etree.ElementTree as ET
import re
from xml.etree import ElementTree
from xml.dom import minidom

app = Flask(__name__)
CORS(app)


def buscarservicio(listaservicio, tipo, nombre):
    for element in listaservicio:
        if element['nombreserv'] == nombre:
            if tipo == 'neutro':
                element['neutros'] += 1
                element['total'] += 1
            elif tipo == 'positivo':
                element['positivos'] += 1
                element['total'] += 1

            elif tipo == 'negativo':
                element['negativos'] += 1
                element['total'] += 1


def buscarempresa(listaempresa, tipo, nombre):
    for element in listaempresa:
        if element['nombre'] == nombre:
            if tipo == 'neutro':
                element['neutros'] += 1
                element['total'] += 1

            elif tipo == 'positivo':
                element['positivos'] += 1
                element['total'] += 1

            elif tipo == 'negativo':
                element['negativos'] += 1
                element['total'] += 1


def normalize(s):
    replacements = (
        ("á", "a"),
        ("é", "e"),
        ("í", "i"),
        ("ó", "o"),
        ("ú", "u"),
        ('ñ', 'n'),
        ('.', ''),
        (',', ''),
        ('\n', ''),
        ('\t', ''),

    )
    for a, b in replacements:
        s = s.replace(a, b).replace(a.upper(), b.upper())
    s = s.lower()
    return s


def prettify(elem):
    """Return a pretty-printed XML string for the Element.
    """
    rough_string = ElementTree.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")


def buildxml(lista, empresas, servicios):
    listrespuestas = ET.Element('lista_respuestas')

    for date in lista:
        respuesta = ET.SubElement(listrespuestas, 'respuesta')
        fecha = ET.SubElement(respuesta, 'respuesta')
        fecha.text = (str)(date['fecha'])
        mensajes = ET.SubElement(respuesta, 'mensajes')
        total = ET.SubElement(mensajes, 'total')
        total.text = (str)(date['total'])
        positivos = ET.SubElement(mensajes, 'positivos')
        positivos.text = (str)(date['positivos'])
        negativos = ET.SubElement(mensajes, 'negativos')
        negativos.text = (str)(date['negativos'])
        neutros = ET.SubElement(mensajes, 'neutros')
        neutros.text = (str)(date['neutros'])

    data = prettify(listrespuestas)
    file = open(f'salidaXML.xml', 'w')

    file.write(data)
    file.close()


def leerxml(xml):
    contadormensajes = 0
    cantidadtotal = 0
    mensajesar = []
    listposi = []
    listnega = []
    listaempresas = []
    aux = []
    listanalizadoempresa = []
    listanalizadoservicio = []
    listaFINAL = []

    root = ET.fromstring(xml)
    for mensajes in root.iter('lista_mensajes'):
        for mensaje in mensajes:
            contadormensajes += 1
            mensajefinal = normalize(mensaje.text)
            mensajesar.append(mensajefinal)

    for item in root.findall('diccionario'):
        for word in item.find('sentimientos_positivos'):
            listposi.append(normalize(word.text))
        for word in item.find('sentimientos_negativos'):
            listnega.append(normalize(word.text))
        for empresas in item.find('empresas_analizar'):
            for empresa in empresas:
                empresss = {}
                servicioalias = []
                if normalize(empresa.text) != '' and normalize(empresa.text) != ' ':
                    nombreempresa = normalize(empresa.text)

                if empresa.tag == 'servicio':
                    servioprestado = empresa.attrib['nombre']
                    servicioalias.append(normalize(servioprestado))
                    for servicios in empresa:
                        alias = servicios.text
                        servicioalias.append(normalize(alias))

                if len(servicioalias) > 0:
                    empresss = {
                        'nombre': nombreempresa,
                        'servicios': servicioalias

                    }
                    listaempresas.append(empresss)

    for em in listaempresas:
        msgxempresa = {
            'nombre': '',
            'fecha': '',
            'total': 0,
            'positivos': 0,
            'negativos': 0,
            'neutros': 0,
        }
        msgxservicio = {
            'nombreempresa': '',
            'fecha': '',
            'nombreserv': '',
            'alias': None,
            'total': 0,
            'positivos': 0,
            'negativos': 0,
            'neutros': 0,
        }
        msgxempresa['nombre'] = em['nombre']

        listanalizadoempresa.append(msgxempresa)
        msgxservicio['nombreserv'] = em['servicios'][0]
        msgxservicio['alias'] = em['servicios']
        msgxservicio['nombreempresa'] = em['nombre']
        listanalizadoservicio.append(msgxservicio)

    for element in listanalizadoempresa:
        if element not in aux:
            aux.append(element)

    listanalizadoempresa = aux
    contadorderepeticiones = 0
    fechapattern = '\d{1,2}\/\d{1,2}\/\d{4}'
    for msg in mensajesar:

        cantidadpo = 0
        cantidadne = 0
        positivostotal = 0
        negativostotal = 0
        neutrostotal = 0
        cantidadtotal = 0
        x = re.findall(fechapattern, msg)
        date = x[0]
        if contadorderepeticiones == 0:
            listanalizadoempresa[0]['fecha'] = date
        if len(x) > 0:
            for po in listposi:
                p = re.findall("\\b(" + po.strip() + ")\\b", msg)
                if len(p) > 0:
                    cantidadpo += len(p)
            for ne in listnega:
                n = re.findall("\\b(" + ne.strip() + ")\\b", msg)
                if len(n) > 0:
                    cantidadne += len(n)
            for em in listanalizadoempresa:

                y = re.findall("\\b(" + em['nombre'] + ")\\b", msg)
                empresaxmsg = em['nombre']
                if len(y) > 0:
                    if cantidadpo == cantidadne:
                        buscarempresa(listanalizadoempresa, 'neutro', empresaxmsg)
                    elif cantidadpo > cantidadne:
                        buscarempresa(listanalizadoempresa, 'positivo', empresaxmsg)
                    elif cantidadne > cantidadpo:
                        buscarempresa(listanalizadoempresa, 'negativo', empresaxmsg)

            for em in listanalizadoservicio:
                contador = 0
                longitud = len(em['alias'])
                servicioname = em['nombreserv']
                while contador < longitud - 1:
                    y = re.findall("\\b(" + em['alias'][contador] + ")\\b", msg)
                    if len(y) > 0:
                        if cantidadpo == cantidadne:
                            buscarservicio(listanalizadoservicio, 'neutro', servicioname)
                        elif cantidadpo > cantidadne:
                            buscarservicio(listanalizadoservicio, 'positivo', servicioname)
                        elif cantidadne > cantidadpo:
                            buscarservicio(listanalizadoservicio, 'negativo', servicioname)
                    contador += 1
            if cantidadpo == cantidadne:
                neutrostotal += 1
                cantidadtotal += 1

            elif cantidadpo > cantidadne:
                positivostotal += 1
                cantidadtotal += 1
            elif cantidadne > cantidadpo:
                negativostotal += 1
                cantidadtotal += 1

        for fecha in listanalizadoempresa:
            if fecha['fecha'] == date:
                pass
            else:
                msgxempresa = {
                    'nombre': fecha['nombre'],
                    'fecha': date,
                    'total': cantidadtotal,
                    'positivos': positivostotal,
                    'negativos': negativostotal,
                    'neutros': neutrostotal,
                }
                listanalizadoempresa.append(msgxempresa)

                break

        if len(listaFINAL) == 0:
            respuestafinalFecha = {
                'fecha': x[0],
                'total': cantidadtotal,
                'positivos': positivostotal,
                'negativos': negativostotal,
                'neutros': neutrostotal,
            }
            listaFINAL.append(respuestafinalFecha)
        else:
            for fecha in listaFINAL:
                if fecha['fecha'] == x[0]:
                    fecha['total'] += cantidadtotal
                    fecha['positivos'] += positivostotal
                    fecha['negativos'] += negativostotal
                    fecha['neutros'] += neutrostotal
                else:
                    respuestafinalFecha = {
                        'fecha': x[0],
                        'total': cantidadtotal,
                        'positivos': positivostotal,
                        'negativos': negativostotal,
                        'neutros': neutrostotal,
                    }
                    listaFINAL.append(respuestafinalFecha)
                    break
        contadorderepeticiones+=1


    buildxml(listaFINAL)
    print('finalie')


@app.route("/medicine", methods=["GET"])
def getMedicine():
    return jsonify([{'name': 'Tabletas', 'price': 10.88}, {'name': 'Curitas', 'price': 12.11}])


@app.route("/palabras", methods=["POST"])
def getxml():
    body = request.get_json()
    xml = body['info']
    leerxml(xml)

    return jsonify({'data': 'Conexcion'})


@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'


if __name__ == '__main__':
    app.run()
