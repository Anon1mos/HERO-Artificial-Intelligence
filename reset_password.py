"""Redefine a senha de uma conta da HERO. Precisa ser executado no computador onde a HERO está instalado.

Uso:  python reset_password.py NOME_DO_USUARIO
"""
import sys, getpass
import core
from auth import hash_pw


def reset(username, new_password):
    if len(new_password) < 8 or len(new_password) > 128:
        raise ValueError("A senha deve ter de 8 a 128 caracteres.")
    rows = core.q("SELECT id FROM users WHERE username=?", (username.strip(),))[0]
    if not rows:
        raise LookupError("Usuário não encontrado.")
    uid = rows[0]["id"]
    core.q("UPDATE users SET pw=? WHERE id=?", (hash_pw(new_password), uid))
    core.q("DELETE FROM sessions WHERE user_id=?", (uid,))     # encerra todas as sessões abertas
    return uid


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    nome = sys.argv[1]
    a, b = getpass.getpass("Nova senha: "), getpass.getpass("Repita a nova senha: ")
    if a != b:
        sys.exit("As senhas não coincidem.")
    try:
        reset(nome, a)
    except (ValueError, LookupError) as e:
        sys.exit(str(e))
    print(f"Senha de '{nome}' redefinida. Todas as sessões abertas foram encerradas.")


if __name__ == "__main__":
    main()
