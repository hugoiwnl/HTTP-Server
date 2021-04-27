"""An example of a simple HTTP server."""
import json
import mimetypes
import pickle
import socket
from os.path import isdir
from urllib.parse import unquote_plus


# Pickle file for storing data
PICKLE_DB = "db.pkl"

# Directory containing www data
WWW_DATA = "www-data"

# Header template for a successful HTTP request
HEADER_RESPONSE_200 = """HTTP/1.1 200 OK\r
content-type: %s\r
content-length: %d\r
connection: Close\r
\r
"""

# Represents a table row that holds user data
TABLE_ROW = """
<tr>
    <td>%d</td>
    <td>%s</td>
    <td>%s</td>
</tr>
"""

# Template for a 404 (Not found) error
RESPONSE_404 = """HTTP/1.1 404 Not found\r
content-type: text/html\r
connection: Close\r
\r
<!doctype html>
<h1>404 Page not found</h1>
<p>Page cannot be found.</p>
"""

RESPONSE_400="""HTTP/1.1 400 Bad request\r
content-type: text/html\r
connection: Close\r
 \r
<!doctype html>
<h1>Bad Request</h1>
<p>Your browser sent a request that this server could not understand.</p>
<p>The request line contained invalid characters following the protocol string.</p>
 """

RESPONSE_405="""HTTP/1.1 405 Method not allowed\r
content-type: text/html\r
connection: Close\r
\r
<!doctype html>
<h1>405 Page Not Allowed</h1>
<p>Mehod Not Allowed</p>
 """

RESPONSE_301="""HTTP/1.1 301 Moved Permanently\r
Location: %s

"""
dodat=False

def save_to_db(first, last):
    """Create a new user with given first and last name and store it into
    file-based database.

    For instance, save_to_db("Mick", "Jagger"), will create a new user
    "Mick Jagger" and also assign him a unique number.

    Do not modify this method."""

    existing = read_from_db()
    existing.append({
        "number": 1 if len(existing) == 0 else existing[-1]["number"] + 1,
        "first": first,
        "last": last
    })
    with open(PICKLE_DB, "wb") as handle:
        pickle.dump(existing, handle)


def read_from_db(criteria=None):
    """Read entries from the file-based DB subject to provided criteria

    Use this method to get users from the DB. The criteria parameters should
    either be omitted (returns all users) or be a dict that represents a query
    filter. For instance:
    - read_from_db({"number": 1}) will return a list of users with number 1
    - read_from_db({"first": "bob"}) will return a list of users whose first
    name is "bob".

    Do not modify this method."""
    if criteria is None:
        criteria = {}
    else:
        # remove empty criteria values
        for key in ("number", "first", "last"):
            if key in criteria and criteria[key] == "":
                del criteria[key]

        # cast number to int
        if "number" in criteria:
            criteria["number"] = int(criteria["number"])

    try:
        with open(PICKLE_DB, "rb") as handle:
            data = pickle.load(handle)

        filtered = []
        for entry in data:
            predicate = True

            for key, val in criteria.items():
                if val != entry[key]:
                    predicate = False

            if predicate:
                filtered.append(entry)

        return filtered
    except (IOError, EOFError):
        return []

def parse_headers(client):
    headers=dict()
    while True:
        line=client.readline().decode("utf-8").strip()
        if not line:
            return headers
        key,value=line.split(":",1)
        headers[key.strip()]=value.strip()
def parse_headers1(client):
    headers = dict()
    while True:
        line = client.readline().decode("utf-8").strip()
        if not line:
            return headers
        headers[line] = "kljuc"


def process_request(connection, address):
    """Process an incoming socket request.

    :param connection is a socket of the client
    :param address is a 2-tuple (address(str), port(int)) of the client
    """
    global put, parametri, prvi, drugi
    client=connection.makefile("wrb")
    # Read and parse the request line
    line=client.readline().decode("utf-8").strip()
    try:
        metoda, uri, version = line.split()
        headers = parse_headers(client)
        tip,enc=mimetypes.guess_type(WWW_DATA + "/" + uri)
        if(tip==None):
            tip="application/octet-stream"
        #provera da li je metoda dobra
        if(metoda!="GET" and metoda!="POST"):
            client.write(RESPONSE_405.encode("utf-8"))
            client.close()
        #provera da li je URL i protokol dobrog oblika
        if((uri[0]!="/" or len(uri)<1)or(version!="HTTP/1.1")):
            client.write(RESPONSE_400.encode("utf-8"))
            client.close()
        if("app-index" in uri and metoda!="GET"):
            client.write(RESPONSE_405.encode("utf-8"))
            client.close()
        if ("app-add" in uri and metoda != "POST"):
            client.write(RESPONSE_405.encode("utf-8"))
            client.close()
        if (metoda == "GET"):
            if ("app-index" in uri):
                #novi pokusaj
                par = uri.split("app-index")[1]
                parametri=par[1:].split("&")
                params=dict()
                filter=dict()
                for p in parametri:
                    if(len(p)>0):
                        key,value=p.split("=")
                        params[key]=value
                for f in params.keys():
                    if(len(params[f])>0):
                        filter[f]=params[f]
                students=read_from_db(filter)
                table = ""
                for student in students:
                    table += TABLE_ROW % (student["number"],
                                          student["first"],
                                          student["last"])
                with open("www-data/app_list.html", "rb") as handle:
                    body = handle.read()
                    telo=body.decode("utf-8")
                    telo=telo.replace("{{students}}", table)
                    head = HEADER_RESPONSE_200 % (
                        "text/html",
                        len(telo)
                    )
                    client.write(head.encode("utf-8"))
                    client.write(telo.encode("utf-8"))
                    client.close()

            elif("app-json" in uri):
                podatki=json.dumps(read_from_db())
                head = HEADER_RESPONSE_200 % (
                    "application/json",
                    len(podatki)
                )
                client.write(head.encode("utf-8"))
                client.write(podatki.encode("utf-8"))



            else:
                if ("Host" not in headers or headers==None):
                    client.write(RESPONSE_400.encode("utf-8"))
                    client.close()
                else:
                    #path = "http://" + headers["Host"] + uri
                    if (uri.endswith("/")):
                        uri += "index.html"
                        head = RESPONSE_301 % ("http://" + headers["Host"] + uri)
                        client.write(head.encode("utf-8"))
                    elif not isdir(uri) and "." not in uri:
                        uri += "/index.html"
                        head = RESPONSE_301 % ("http://" + headers["Host"] + uri)
                        client.write(head.encode("utf-8"))
                    #client.close()
                    try:
                        if("www-data" not in uri):
                            put="/www-data"+uri

                        with open(put[1:], "rb") as handle:
                            body = handle.read()
                        head = HEADER_RESPONSE_200 % (
                            tip,
                            len(body)
                        )
                        client.write(head.encode("utf-8"))
                        client.write(body)
                    except FileNotFoundError as e:
                        client.write(RESPONSE_404.encode("utf-8"))
                        client.close()
        if(metoda == "POST"):
            if("Content-Length" not in headers or headers==None):
                print("nema cont len")
                client.write(RESPONSE_400.encode("utf-8"))
                client.close()
            else:
                if("Content-Type" in headers):
                    if(headers["Content-Type"]!="application/x-www-form-urlencoded"):
                        print("nema type")
                        client.write(RESPONSE_400.encode("utf-8"))
                        client.close()
                try:
                    lastline=client.read(int(headers["Content-Length"]))
                    parametri=lastline.decode("utf-8")
                    prvi,drugi=parametri.split("&")
                except:
                    client.write(RESPONSE_400.encode("utf-8"))
                    client.close()
                if(uri=="/app-add"):
                    if("first" not in parametri or "last" not in parametri):
                        client.write(RESPONSE_400.encode("utf-8"))
                        client.close()
                    else:
                        save_to_db(prvi[6:],drugi[5:])
                        tip, enc = mimetypes.guess_type("www-data/app_add.html")
                        with open("www-data/app_add.html", "rb") as handle:
                            body = handle.read()
                        head = HEADER_RESPONSE_200 % (
                            tip,
                            len(body)
                        )
                        client.write(head.encode("utf-8"))
                        client.write(body)




        #citanje fajla
    except (ValueError, AssertionError,IOError):
        client.write(RESPONSE_400.encode("utf-8"))

    # Read and parse headers

    # Read and parse the body of the request (if applicable)

    # create the response
    # Write the response back to the socket
    finally:
        client.close()
def main(port):
    """Starts the server and waits for connections."""

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("", port))
    server.listen(1)

    print("Listening on %d" % port)

    while True:
        connection, address = server.accept()

        print("[%s:%d] CONNECTED" % address)
        process_request(connection, address)
        connection.close()
        print("[%s:%d] DISCONNECTED" % address)


if __name__ == "__main__":
    main(8080)
