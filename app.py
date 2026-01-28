from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/fotos'

# Garante que a pasta de fotos exista
if not os.path.isdir(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def conectar():
    con = sqlite3.connect("estoque.db")
    con.row_factory = sqlite3.Row
    return con

def criar_tabelas():
    con = conectar()
    cur = con.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS itens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            descricao TEXT,
            armario TEXT,
            quantidade INTEGER,
            foto TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS followup (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER,
            quem TEXT,
            motivo TEXT,
            quantidade INTEGER,
            data TEXT
        )
    """)

    con.commit()
    con.close()

@app.route("/")
def index():
    con = conectar()
    itens = con.execute("SELECT * FROM itens").fetchall()
    con.close()
    return render_template("index.html", itens=itens)

@app.route("/novo", methods=["GET", "POST"])
def novo_item():
    if request.method == "POST":
        nome = request.form["nome"]
        descricao = request.form["descricao"]
        armario = request.form["armario"]
        quantidade = int(request.form["quantidade"])
        foto = request.files.get("foto")

        nome_foto = None
        if foto and foto.filename != "":
            nome_foto = secure_filename(foto.filename)
            foto.save(os.path.join(app.config['UPLOAD_FOLDER'], nome_foto))

        con = conectar()
        con.execute("""
            INSERT INTO itens (nome, descricao, armario, quantidade, foto)
            VALUES (?, ?, ?, ?, ?)
        """, (nome, descricao, armario, quantidade, nome_foto))
        con.commit()
        con.close()

        return redirect(url_for("index"))

    return render_template("novo_item.html")

@app.route("/item/<int:id>", methods=["GET", "POST"])
def item(id):
    con = conectar()
    cur = con.cursor()

    if request.method == "POST":
        acao = request.form.get("acao")
        qtd_input = request.form.get("quantidade")

        if acao and qtd_input:
            qtd = int(qtd_input)
            quem = request.form.get("quem", "Sistema")
            motivo = request.form.get("motivo", acao)

            if acao == "retirada":
                cur.execute(
                    "UPDATE itens SET quantidade = quantidade - ? WHERE id = ?",
                    (qtd, id)
                )
                cur.execute("""
                    INSERT INTO followup (item_id, quem, motivo, quantidade, data)
                    VALUES (?, ?, ?, ?, ?)
                """, (id, quem, motivo, -qtd, datetime.now().strftime("%d/%m/%Y %H:%M")))

            elif acao == "adicao":
                cur.execute(
                    "UPDATE itens SET quantidade = quantidade + ? WHERE id = ?",
                    (qtd, id)
                )
                cur.execute("""
                    INSERT INTO followup (item_id, quem, motivo, quantidade, data)
                    VALUES (?, ?, ?, ?, ?)
                """, (id, quem, motivo, qtd, datetime.now().strftime("%d/%m/%Y %H:%M")))

            con.commit()
            return redirect(url_for("item", id=id))

    item = cur.execute("SELECT * FROM itens WHERE id = ?", (id,)).fetchone()
    historico = cur.execute("""
        SELECT quem, motivo, quantidade, data
        FROM followup
        WHERE item_id = ?
        ORDER BY id DESC
    """, (id,)).fetchall()

    con.close()
    return render_template("item.html", item=item, historico=historico)

@app.route("/editar/<int:id>", methods=["GET", "POST"])
def editar_item(id):
    con = conectar()
    cur = con.cursor()

    if request.method == "POST":
        nome = request.form["nome"]
        descricao = request.form["descricao"]
        armario = request.form["armario"]
        quantidade = int(request.form["quantidade"])
        foto = request.files.get("foto")

        if foto and foto.filename != "":
            nome_foto = secure_filename(foto.filename)
            foto.save(os.path.join(app.config['UPLOAD_FOLDER'], nome_foto))
            cur.execute("""
                UPDATE itens
                SET nome=?, descricao=?, armario=?, quantidade=?, foto=?
                WHERE id=?
            """, (nome, descricao, armario, quantidade, nome_foto, id))
        else:
            cur.execute("""
                UPDATE itens
                SET nome=?, descricao=?, armario=?, quantidade=?
                WHERE id=?
            """, (nome, descricao, armario, quantidade, id))

        con.commit()
        con.close()
        return redirect(url_for("item", id=id))

    item = cur.execute("SELECT * FROM itens WHERE id = ?", (id,)).fetchone()
    con.close()
    return render_template("editar_item.html", item=item)

@app.route("/relatorio")
def relatorio():
    con = conectar()
    itens = con.execute("""
        SELECT nome, armario, quantidade
        FROM itens
        ORDER BY nome
    """).fetchall()
    con.close()

    return render_template("relatorio.html", itens=itens)

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
