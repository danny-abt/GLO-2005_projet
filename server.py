from flask import Flask, render_template, request, redirect, url_for, session, flash # session → pour garder l’utilisateur connecté (session['user_id']) et sert à garder des infos entre les pages
from werkzeug.security import generate_password_hash, check_password_hash
from pymysql.err import IntegrityError, OperationalError, DataError #Pour les erreurs qu'on crée avec SIGNAL SQLSTATE '45000'
import pymysql
import pymysql.cursors

app = Flask(__name__)
app.secret_key = "ma_cle_secrete_flask"  # Clé secrète pour sécuriser les cookies de session



# Fonction de connexion à MySQL
def get_db_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='root',     # Mot de passe MySQL
        db='GLO_PROJET',
        charset='utf8mb4',   # Pour gérer les caractères spéciaux
        cursorclass=pymysql.cursors.DictCursor   # Pour accéder aux colonnes par nom(clé valeeur comme dictionnaire) Exemple (user['username'])
    )

@app.route('/')
def index():
    return redirect(url_for('login'))

# Page de connexion (GET : afficher le formulaire / POST : traitement de la connexion)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form['identifier']
        password = request.form['password']
        selected_role = request.form['role']

        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM users
                    WHERE (username = %s OR email = %s) AND role = %s
                """, (identifier, identifier, selected_role))
                user = cursor.fetchone()
        finally:
            conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']

            if user['role'] == 'conseiller':
                conn = get_db_connection()
                try:
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT id FROM conseillers WHERE id_user = %s", (user['id'],))
                        conseiller = cursor.fetchone()
                        if conseiller:
                            session['id'] = conseiller['id']
                finally:
                    conn.close()

            return redirect(url_for('admin_dashboard' if user['role'] == 'admin' else 'conseiller_dashboard'))

        return render_template('login.html', error="Identifiants incorrects")

    return render_template('login.html')



###############
#  ADMIN
###############

# Tableau de bord admin (affiche son profil)
@app.route('/admin')
def admin_dashboard():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    user_id = session['user_id']
    admin_info = None

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            
            cmd = """SELECT nom, prenom, sexe, poste, langue, adresse, nas
                     FROM admin
                     WHERE id_user = %s"""
            cursor.execute(cmd, (user_id,))
            admin_info = cursor.fetchone()
    finally:
        conn.close()

    return render_template('admin_dashboard.html', admin=admin_info)




@app.route('/admin/edit_profils', methods=['GET', 'POST'])
def admin_edit_profils():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    user_id = session['user_id']
    error = None
    success = None
    donnée_actuelle = None  # définie dès le début

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            if request.method == 'POST':
                new_username = request.form['username']
                new_password = request.form['password']
                new_email = request.form['email']
                hashed_password = generate_password_hash(new_password)

                cursor.execute("SELECT id FROM users WHERE (username = %s OR email = %s) AND id != %s",
                               (new_username, new_email, user_id))
                if cursor.fetchone():
                    error = "Nom d'utilisateur ou email déjà pris."
                else:
                    cursor.execute("""UPDATE users 
                                      SET username = %s, email = %s, password = %s 
                                      WHERE id = %s""",
                                   (new_username, new_email, hashed_password, user_id))
                    conn.commit()
                    session['username'] = new_username
                    success = "Informations mises à jour avec succès."

            # Toujours exécuté (GET ou POST)
            cursor.execute("SELECT username, email FROM users WHERE id = %s", (user_id,))
            donnée_actuelle = cursor.fetchone()
    except IntegrityError as e:
            error = "Erreur lors de l'enregistrement"
    except DataError:
            error = "Erreur lors de l'enregistrement : une donnée est trop longue ou invalide."
    finally:
        conn.close()

    return render_template("admin_edit_profils.html", error=error, success=success, user=donnée_actuelle)





@app.route('/admin/modifier_profil', methods=['GET', 'POST'])
def admin_modifier_profil():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    user_id = session['user_id']
    success = None
    error = None
    admin = None

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            if request.method == 'POST':
                nom = request.form['nom']
                prenom = request.form['prenom']
                sexe = request.form['sexe']
                adresse = request.form['adresse']
                nas = request.form['nas'].replace(" ", "")
                langue = request.form['langue']

                # Vérifie si NAS est déjà utilisé dans la table conseiller
                cursor.execute("SELECT id FROM conseillers WHERE nas = %s", (nas,))
                if cursor.fetchone():
                    error = "Ce NAS est déjà utilisé par un conseiller."
                else:
                    cursor.execute("""
                        UPDATE admin SET nom = %s, prenom = %s, sexe = %s, adresse = %s, nas = %s, langue = %s
                        WHERE id_user = %s
                    """, (nom, prenom, sexe, adresse, nas, langue,user_id))
                    conn.commit()
                    success = "Profil mis à jour avec succès."

            cursor.execute("SELECT * FROM admin WHERE id_user = %s", (user_id,))
            admin = cursor.fetchone()

    except IntegrityError as e:
            error = "Erreur lors de l'enregistrement"
    except DataError:
            error = "Erreur lors de l'enregistrement : une donnée est trop longue ou invalide."
    finally:
        conn.close()

    return render_template("admin_modifier_profil.html", admin=admin, success=success, error=error)






# Liste des conseillers
@app.route('/admin/conseillers')
def admin_conseillers():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    recherche = request.args.get('recherche', '').strip()
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            if recherche:
                cmd = """
                    SELECT c.id, c.nom, c.prenom, c.salaire, u.username
                    FROM conseillers c
                    JOIN users u ON c.id_user = u.id
                    WHERE c.nas LIKE %s OR c.nom LIKE %s OR c.numero_permis LIKE %s
                """
                val = f"%{recherche.replace(' ', '')}%"
                cursor.execute(cmd, (val, val, val))
            else:  #Jointure pour affichier le username de chaque conseillers
                cmd = """
                    SELECT c.id, c.nom, c.prenom, c.salaire, u.username  
                    FROM conseillers c
                    JOIN users u ON c.id_user = u.id
                """
                cursor.execute(cmd)
            liste_conseillers = cursor.fetchall()
    finally:
        conn.close()

    return render_template('admin_conseillers.html', conseillers=liste_conseillers)


# Détail d'un conseiller (profil)
@app.route('/admin/conseiller/<int:id>')  # <a href="{{ url_for('admin_view_conseiller', id=c.id) }}"
def admin_view_conseiller(id):  #Flask lit l’id dans l’URL #pour que id soit en entrée pour identifier le conseiller
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    conseiller = None

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Récupérer les infos du conseiller 
            cmd = """SELECT c.id, c.nom, c.prenom, c.annee_activite, c.numero_permis, c.sexe, c.langue, 
            c.nombre_clients, c.nas, c.type_permis, c.adresse, c.salaire
            FROM conseillers c
            WHERE c.id = %s"""

            cursor.execute(cmd, (id,))
            conseiller = cursor.fetchone()

            # Je veux un affichage NAS avec espace AHAHA
            if conseiller and 'nas' in conseiller and len(conseiller['nas']) == 9:
                conseiller['nas'] = f"{conseiller['nas'][:3]} {conseiller['nas'][3:6]} {conseiller['nas'][6:]}"



    finally:
        conn.close()

    return render_template('admin_conseiller_profil.html',
                           conseiller=conseiller)



@app.route('/admin/create_conseiller', methods=['GET', 'POST'])
def admin_create_conseiller():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    error = None

    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip().lower()      #strip() pour enlever les espaces début et à la fin de la chaîne
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        nom = request.form['nom']
        sexe = request.form['sexe']
        prenom = request.form['prenom']
        salaire = request.form['salaire']
        nas = request.form['nas'].replace(' ', '')
        adresse = request.form['adresse']
        annee_activite = int(request.form['annee_activite'])
        numero_permis = int(request.form['numero_permis'])
        langue = request.form.getlist('langue[]')
        langues_str = ', '.join(langue)

        type_permis = request.form['type_permis']

        

        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                # Appel de la procédure pour insérer dans user si username unique
                cursor.callproc('insert_user_si_username_mail_unique', (
                    username, email, hashed_password, 'conseiller', 0  #0 pour la sortie OUT qui va etre ignore Car dans procedure SET p_user_id = LAST_INSERT_ID();
                ))

                cursor.execute("SELECT LAST_INSERT_ID() AS id;")
                new_user_id = cursor.fetchone()['id']

                # Appel de la procédure pour insérer conseiller si NAS unique
                cursor.callproc('insert_conseiller_si_nas_unique', (
                    new_user_id, nom, prenom, annee_activite, numero_permis, sexe,
                    langues_str, type_permis, salaire, nas, adresse
))


                conn.commit()
                return redirect(url_for('admin_conseillers'))

        except OperationalError as e:
            error_msg = str(e)
            if "Nom d'utilisateur déjà utilisé" in error_msg:
                error = "Nom d'utilisateur déjà utilisé."
            elif "Le NAS est déjà utilisé" in error_msg:
                error = "Ce NAS est déjà utilisé."
            elif "Email déjà utilisé" in error_msg:
                error = "Email déjà utilisé !"
            else:
                error = "Erreur lors de l'enregistrement."

        except IntegrityError as e:
            error_msg = str(e)
            if "users.email" in error_msg:
                error = "Email déjà utilisé."
            if "conseillers.numero_permis" in error_msg:
                error = "Numéro de permis déjà existant"
            else:
                error = "Erreur lors de l'enregistrement"
                
        except DataError:
            error = "Erreur lors de l'enregistrement : une donnée est trop longue ou invalide."


        finally:
            conn.close()

    return render_template('admin_create_conseiller.html', error=error)

@app.route('/admin/delete_conseiller/<int:id>', methods=['POST'])   #<form action="{{ url_for('admin_delete_conseiller', id=conseiller.id) }}"
def admin_delete_conseiller(id):
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Récupérer l'identifiant de l'utilisateur associé au conseiller
            cursor.execute("SELECT id_user FROM conseillers WHERE id = %s", (id,))
            id = cursor.fetchone()
            if id:
                user_id = id['id_user']
                # Supprimer l'utilisateur ; avec ON DELETE CASCADE, le conseiller sera supprimé automatiquement.
                cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
                conn.commit()
    finally:
        conn.close()

    return redirect(url_for('admin_conseillers'))


@app.route('/admin/stats')
def admin_stats():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS total FROM conseillers")
            nb_conseillers = cursor.fetchone()['total']  #La clé du tuple retourné (fectchone) sera "total"

            cursor.execute("SELECT COUNT(*) AS total FROM clients")
            nb_clients = cursor.fetchone()['total']
    finally:
        conn.close()

    return render_template("admin_stats.html", nb_conseillers=nb_conseillers, nb_clients=nb_clients)


###############
#  CONSEILLER
###############

# Tableau de bord du conseiller





###################################
#Page d'acceuil Conseiller
@app.route('/profil')
def conseiller_dashboard():
    if 'role' not in session or session['role'] != 'conseiller':
        return redirect(url_for('login'))

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM conseillers WHERE id_user = %s", (session['user_id'],))
            conseiller = cursor.fetchone()
            session['id'] = conseiller['id']
    finally:
        conn.close()

    return render_template('profil.html', user=conseiller)


@app.route('/conseiller/modifierprofil', methods=['GET', 'POST'])
def conseiller_modifier_profil():
    if 'role' not in session or session['role'] != 'conseiller':
        return redirect(url_for('login'))
    error = None

    if request.method == 'POST':
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM conseillers WHERE id_user = %s", (session['user_id'],))
                conseiller = cursor.fetchone()

                cursor.execute(
                    "UPDATE conseillers SET adresse = %s WHERE id = %s",
                    (request.form['adresse'], session['id'])
                )
                conn.commit()
                return redirect(url_for('conseiller_dashboard'))
        except DataError:
            error = "Erreur lors de l'enregistrement : une donnée est trop longue ou invalide."
        finally:
            conn.close()
            
            
    return render_template('conseiller_modifier_profil.html', error = error)



@app.route('/conseiller/edit_connexion', methods=['GET', 'POST'])
def conseiller_edit_connexion():
    if 'role' not in session or session['role'] != 'conseiller':
        return redirect(url_for('login'))

    user_id = session['user_id']
    error = None
    success = None
    infos = None

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            if request.method == 'POST':
                new_username = request.form['username']
                new_password = request.form['password']
                new_email = request.form['email']
                hashed_password = generate_password_hash(new_password)

                # Vérifier si username/email existe déjà chez un autre user
                cursor.execute("""
                    SELECT id FROM users 
                    WHERE (username = %s OR email = %s) AND id != %s
                """, (new_username, new_email, user_id))
                if cursor.fetchone():
                    error = "Nom d'utilisateur ou email déjà utilisé."
                else:
                    # Vérifier que le mail n’est pas dans clients
                    cursor.execute("SELECT id FROM clients WHERE mail = %s", (new_email,))
                    if cursor.fetchone():
                        error = "Email déjà utilisé par un client."
                    else:
                        cursor.execute("""
                            UPDATE users SET username = %s, email = %s, password = %s 
                            WHERE id = %s
                        """, (new_username, new_email, hashed_password, user_id))
                        conn.commit()
                        session['username'] = new_username
                        success = "Informations mises à jour avec succès."

            cursor.execute("SELECT username, email FROM users WHERE id = %s", (user_id,))
            infos = cursor.fetchone()

    except DataError:
            error = "Erreur lors de l'enregistrement : une donnée est trop longue ou invalide."       
    finally:
        conn.close()

    return render_template("conseiller_edit_connexion.html", user=infos, error=error, success=success)



# Liste des clients
@app.route('/clients', methods=['GET', 'POST'])
def clients():
    if 'role' not in session or session['role'] != 'conseiller':
        return redirect(url_for('login'))

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            if request.method == 'POST':
                search = request.form.get('search')
                cursor.execute("""
                    SELECT cl.id, cl.nom, cl.prenom, cl.sexe, cl.mail, cl.profession, cl.etat_civil, cl.id_conseiller, cl.nas
                    FROM clients cl
                    INNER JOIN conseillers co ON cl.id_conseiller = co.id
                    WHERE cl.id_conseiller = %s AND (cl.nas = %s OR cl.nom = %s)
                """, (session['id'], search, search))
                clients = cursor.fetchall()
            else:
                cursor.execute("""
                    SELECT cl.id, cl.nom, cl.prenom, cl.sexe, cl.mail, cl.profession, cl.etat_civil, cl.id_conseiller
                    FROM clients cl
                    INNER JOIN conseillers co ON cl.id_conseiller = co.id
                    WHERE cl.id_conseiller = %s
                """, (session['id'],))
                clients = cursor.fetchall()
    finally:
        conn.close()

    return render_template("clients.html", clients=clients)



#Page pour profil client
# Voir un client
@app.route('/profilclient/<int:id>')
def profil_client(id):
    if 'role' not in session or session['role'] != 'conseiller':
        return redirect(url_for('login'))

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM clients WHERE id = %s", (id,))
            client = cursor.fetchone()
            cursor.execute("""
                SELECT * FROM contrats cont
                INNER JOIN clients cl ON cont.nas_client = cl.nas
                WHERE cl.id = %s
            """, (id,))
            contrats = cursor.fetchall()
    finally:
        conn.close()

    return render_template("profilclient.html", client=client, contrats=contrats)





#Page pour ajout client
# Création d'un client
# Page pour ajout client
# Création d'un client
@app.route('/conseiller/ajoutclient', methods=['GET', 'POST'])
def conseiller_ajout_client():
    if 'role' not in session or session['role'] != 'conseiller':
        return redirect(url_for('login'))

    error = None

    if request.method == 'POST':
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                # Vérification NAS
                cursor.callproc('verifier_nas_client_contrat', (
                    request.form.get('nas'),
                    'clients',
                    session.get('id')
                ))

                # Vérification mail
                cursor.callproc('verifier_mail_client', (
                    request.form.get('mail'),
                ))

                values = (
                    request.form['nom'],
                    request.form['prenom'],
                    request.form['mail'],
                    request.form['revenu_annuel'],
                    request.form['etat_civil'],
                    request.form['situation_habitation'],
                    request.form['sexe'],
                    request.form['langue'],
                    request.form['profession'],
                    request.form['statut_canada'],
                    request.form['nas'],
                    request.form['adresse'],
                    session['id']
                )

                cursor.execute("""
                    INSERT INTO clients (
                        nom, prenom, mail, revenu_annuel, etat_civil,
                        situation_habitation, sexe, langue, profession,
                        Statut_canada, nas, adresse, id_conseiller
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, values)
                conn.commit()
                return redirect(url_for('conseiller_ajout_contrat'))

        except pymysql.err.OperationalError as error:
            message = str(error.args[1])
            if 'NAS existant' in message:
                flash(message, "error")
            elif 'Un conseiller ne peut pas etre un client' in message:
                flash(message, "error")
            elif 'Un Admin ne peut pas etre un client' in message:
                flash(message, "error")
            elif 'Adresse courriel déjà utilisée' in message or message == 'a':
                flash("Adresse courriel déjà utilisée", "error")
            return render_template('conseiller_ajout_client.html')

        except DataError:
            error = "Erreur lors de l'enregistrement : une donnée est trop longue ou invalide."

        finally:
            conn.close()

    return render_template('conseiller_ajout_client.html', error=error)







#Page modification client
@app.route('/modifierclient/<int:id>', methods=['GET', 'POST'])
def modifier_client(id):
    if 'role' not in session or session['role'] != 'conseiller':
        return redirect(url_for('login'))

    error = None

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM clients WHERE id = %s", (id,))
            client = cursor.fetchone()
    finally:
        conn.close()

    if request.method == 'POST':
        form = {k: request.form.get(k) or client[k] for k in client}
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE clients SET mail=%s, profession=%s,
                    etat_civil=%s, situation_habitation=%s, Statut_canada=%s,
                    adresse=%s, revenu_annuel=%s
                    WHERE id = %s
                """, (
                    form['mail'], form['profession'], form['etat_civil'],
                    form['situation_habitation'], form['Statut_canada'],
                    form['adresse'], form['revenu_annuel'], id
                ))
                conn.commit()
                flash("Profil client modifié avec succès", "success")
        except DataError:
            error = "Erreur lors de l'enregistrement : une donnée est trop longue ou invalide."
        finally:
            conn.close()

        if error:
            return render_template('modifier_client.html', client=client, error=error)

        return redirect(url_for('modifier_client', id=id))

    return render_template('modifier_client.html', client=client)



    #Supprimer Client
# Supprimer un client
@app.route('/supprimerclient/<int:id>')
def supprimer_client(id):
    if 'role' not in session or session['role'] != 'conseiller':
        return redirect(url_for('login'))

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM clients WHERE id = %s", (id,))
            conn.commit()
    finally:
        conn.close()

    return redirect(url_for('clients'))




#Page liste contrat
@app.route('/contrat', methods=['GET', 'POST'])
def contrat():
    if 'role' not in session or session['role'] != 'conseiller':
        return redirect(url_for('login'))

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            if request.method == 'POST':
                search = request.form.get('search')
                cursor.execute("""
                    SELECT * FROM (SELECT * FROM contrats WHERE nas_client IN (
                        SELECT cl.nas FROM clients cl INNER JOIN conseillers co ON cl.id_conseiller = co.id WHERE co.id = %s
                    )) AS search WHERE nas_client = %s
                """, (session['id'], search))
                contrats = cursor.fetchall()
            else:
                cursor.execute("""
                    SELECT * FROM contrats WHERE nas_client IN (
                        SELECT cl.nas FROM clients cl INNER JOIN conseillers co ON cl.id_conseiller = co.id WHERE co.id = %s
                    )
                """, (session['id'],))
                contrats = cursor.fetchall()
    finally:
        conn.close()

    return render_template("contrat.html", contrats=contrats)






    #Page voir contrat
@app.route('/profilcontrat/<int:id>')
def profil_contrat(id):
    if 'role' not in session or session['role'] != 'conseiller':
        return redirect(url_for('login'))

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM contrats WHERE numero = %s", (id,))
            contrat = cursor.fetchone()
            cursor.execute("""
                SELECT * FROM clients cl INNER JOIN contrats cont ON cl.nas = cont.nas_client WHERE cont.numero = %s
            """, (id,))
            client = cursor.fetchone()
    finally:
        conn.close()

    return render_template("profil_contrat.html", contrat=contrat, client=client)

    



    #Page ajout Contrat
@app.route('/conseiller/ajoutcontrat', methods=['GET', 'POST'])
def conseiller_ajout_contrat():
    if 'role' not in session or session['role'] != 'conseiller':
        return redirect(url_for('login'))
    
    error = None

    if request.method == 'POST':
        nas_client = request.form['nas_client']
        nombre_annees = request.form['nombre_annees']
        id_risque = request.form['id_risque']
        type_compte = request.form['type_compte']
        taux_interet = request.form['taux_interet']
        beneficiaires = request.form['beneficiaires']
        mont_initial = request.form['mont_initial']
        mont_mensuel = request.form['mont_mensuel']

        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.callproc('verifier_nas_client_contrat', (
                    request.form.get('nas_client'), 'contrats', session.get('id')
                ))
                #cursor.callproc('verifier_nas_client_contrat', (request.form.get('nas'), 'contrats', session.get('id')))

                cursor.execute("""
                    INSERT INTO contrats (
                        nas_client, nombre_annees, id_risque, type_compte,
                        taux_interet, beneficiaires, mont_initial, mont_mensuel
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    nas_client, nombre_annees, id_risque, type_compte,
                    taux_interet, beneficiaires, mont_initial, mont_mensuel
                ))
                conn.commit()
                return redirect(url_for('conseiller_ajout_contrat'))

        except pymysql.err.OperationalError as error:
            if 'NAS client inexistant ou pas parmi vos clients' in error.args[1]:
                message = str(error.args[1])
                flash(message, "error")
                return render_template('conseiller_ajout_contrat.html')
        except DataError:
            error = "Erreur lors de l'enregistrement : une donnée est trop longue ou invalide."
        finally:
            conn.close()

    return render_template('conseiller_ajout_contrat.html', error = error)






#Page modification contrat
@app.route('/modifiercontrat/<int:numero>', methods=['GET', 'POST'])
def modifier_contrat(numero):
    if 'role' not in session or session['role'] != 'conseiller':
        return redirect(url_for('login'))

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM contrats WHERE numero = %s", (numero,))
            contrat = cursor.fetchone()
    finally:
        conn.close()

    if request.method == 'POST':
        form = {k: request.form.get(k) or contrat[k] for k in contrat}

        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE contrats SET nombre_annees = %s, id_risque = %s, type_compte = %s,
                    taux_interet = %s, beneficiaires = %s, mont_initial = %s, mont_mensuel = %s
                    WHERE numero = %s
                """, (
                    form['nombre_annees'], form['id_risque'], form['type_compte'],
                    form['taux_interet'], form['beneficiaires'], form['mont_initial'],
                    form['mont_mensuel'], numero
                ))
                conn.commit()
        finally:
            conn.close()

        return redirect(url_for('profil_contrat', id=numero))
    
    return render_template('modifier_contrat.html', contrat=contrat)


    


    # Supprimer Contrat
@app.route('/supprimercontrat/<int:numero>')
def supprimer_contrat(numero):
    if 'role' not in session or session['role'] != 'conseiller':
        return redirect(url_for('login'))

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM contrats WHERE numero = %s", (numero,))
            conn.commit()
    finally:
        conn.close()

    return redirect(url_for('contrat'))




###################################

# Déconnexion : vide la session
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
