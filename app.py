import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/fotos'

if not os.path.isdir(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def conectar():
    # Caminho absoluto ajuda a evitar erros de permissão no Render
    base_dir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(base_dir, "estoque.db")
    con = sqlite3.connect(db_path)
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
            foto TEXT,
            categoria TEXT
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
    try:
        con = conectar()
        itens = con.execute("SELECT * FROM itens").fetchall()
        con.close()
        return render_template("index.html", itens=itens)
    except Exception as e:
        return f"Erro no Banco de Dados: {e}. Tente deletar o arquivo estoque.db e reiniciar o app."

@app.route("/novo", methods=["GET", "POST"])
def novo_item():
    if request.method == "POST":
        nome = request.form["nome"]
        descricao = request.form["descricao"]
        armario = request.form["armario"]
        quantidade = int(request.form["quantidade"])
        categoria = request.form.get("categoria", "Sem Categoria")
        foto = request.files.get("foto")

        nome_foto = None
        if foto and foto.filename != "":
            nome_foto = secure_filename(foto.filename)
            foto.save(os.path.join(app.config['UPLOAD_FOLDER'], nome_foto))

        con = conectar()
        con.execute("""
            INSERT INTO itens (nome, descricao, armario, quantidade, foto, categoria)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (nome, descricao, armario, quantidade, nome_foto, categoria))
        con.commit()
        con.close()
        return redirect(url_for("index"))
    return render_template("novo_item.html")

# As outras rotas (item, editar, relatorio) seguem a mesma lógica anterior...
# Certifique-se de que a rota /editar também salve a 'categoria'

@app.route("/editar/<int:id>", methods=["GET", "POST"])
def editar_item(id):
    con = conectar()
    cur = con.cursor()
    if request.method == "POST":
        nome = request.form["nome"]
        descricao = request.form["descricao"]
        armario = request.form["armario"]
        quantidade = int(request.form["quantidade"])
        categoria = request.form["categoria"]
        foto = request.files.get("foto")

        if foto and foto.filename != "":
            nome_foto = secure_filename(foto.filename)
            foto.save(os.path.join(app.config['UPLOAD_FOLDER'], nome_foto))
            cur.execute("""
                UPDATE itens SET nome=?, descricao=?, armario=?, quantidade=?, foto=?, categoria=?
                WHERE id=?
            """, (nome, descricao, armario, quantidade, nome_foto, categoria, id))
        else:
            cur.execute("""
                UPDATE itens SET nome=?, descricao=?, armario=?, quantidade=?, categoria=?
                WHERE id=?
            """, (nome, descricao, armario, quantidade, categoria, id))
        con.commit()
        con.close()
        return redirect(url_for("item", id=id))

    item = cur.execute("SELECT * FROM itens WHERE id = ?", (id,)).fetchone()
    con.close()
    return render_template("editar_item.html", item=item)

if __name__ == "__main__":
    criar_tabelas()
    port = int(os.environ.get("PORT", 10000)) # Render costuma usar 10000 por padrão
    app.run(host="0.0.0.0", port=port)
