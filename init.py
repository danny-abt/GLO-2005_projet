
import pymysql
from werkzeug.security import generate_password_hash

connection = pymysql.connect(
    host="localhost",
    user="root",
    password="root",
    autocommit=True,
)

cursor = connection.cursor()
cursor.execute("DROP DATABASE IF EXISTS GLO_PROJET;")
cursor.execute("CREATE DATABASE IF NOT EXISTS GLO_PROJET;")
cursor.execute("USE GLO_PROJET;")

# TABLE USERS
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INT NOT NULL AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role ENUM('admin', 'conseiller') NOT NULL,
    email VARCHAR(100) UNIQUE,
    PRIMARY KEY (id),
    UNIQUE (email)
);
""")

# TABLE ADMIN
cursor.execute("""
CREATE TABLE IF NOT EXISTS admin (
    id INT NOT NULL AUTO_INCREMENT,
    nom VARCHAR(25),
    prenom VARCHAR(25),
    id_user INT,
    sexe VARCHAR(15),
    poste VARCHAR(100),
    nas CHAR(9) UNIQUE,
    langue VARCHAR(50),
    adresse VARCHAR(255),
    PRIMARY KEY (id),
    FOREIGN KEY (id_user) REFERENCES users(id),
    CHECK (nas REGEXP '^[0-9]{9}$')
);
""")

# TABLE CONSEILLERS
cursor.execute("""
CREATE TABLE IF NOT EXISTS conseillers (
    id INT NOT NULL AUTO_INCREMENT,
    nom VARCHAR(25) NOT NULL,
    prenom VARCHAR(25) NOT NULL,
    annee_activite INT NOT NULL,
    numero_permis INT UNIQUE,
    sexe VARCHAR(15),
    langue VARCHAR(50),
    nombre_clients INT DEFAULT 0,
    nas CHAR(9) UNIQUE NOT NULL,
    type_permis VARCHAR(35),
    adresse VARCHAR(50),
    salaire INT,
    id_user INT NOT NULL UNIQUE,
    PRIMARY KEY(id),
    CONSTRAINT Fk_iduser_id FOREIGN KEY (id_user) REFERENCES users(id) ON DELETE CASCADE
);
""")

# TABLE CLIENTS
cursor.execute("""
CREATE TABLE IF NOT EXISTS clients (
    id INT NOT NULL AUTO_INCREMENT,
    nom VARCHAR(25) NOT NULL,
    prenom VARCHAR(25) NOT NULL,
    mail VARCHAR(50),
    revenu_annuel DECIMAL(8,2) NOT NULL,
    etat_civil VARCHAR(20),
    situation_habitation ENUM('Locataire', 'Propriétaire'),
    sexe VARCHAR(15),
    langue VARCHAR(50),
    profession VARCHAR(50),
    Statut_canada VARCHAR(25),
    nas CHAR(9) UNIQUE NOT NULL,
    adresse VARCHAR(50),
    id_conseiller INT NOT NULL,
    PRIMARY KEY(id),
    CONSTRAINT Fk_id_conseiller_id FOREIGN KEY (id_conseiller) REFERENCES conseillers(id) ON DELETE CASCADE
);
""")

# TABLE RISQUES
cursor.execute("""
CREATE TABLE IF NOT EXISTS risques (
    id INT NOT NULL AUTO_INCREMENT,
    niveau ENUM('Faible', 'Moderé', 'Elevé'),
    descript VARCHAR(100),
    tolerance_perte VARCHAR(20),
    duree VARCHAR(50),
    PRIMARY KEY(id)
);
""")

# Valeurs Table risque 
cursor.execute("""
INSERT INTO risques (id, niveau, descript, tolerance_perte, duree) VALUES 
(1, 'Faible', 'Sécurité maximale, capital protégé', 'Faible (0 á 5%)', 'Court terme (0-2 ans)'),
(2, 'Moderé', 'Mix sécurité/croissance, pertes tolérences', 'Moyenne (5 á 15%)', 'Moyen terme (3-5 ans)'),
(3, 'Elevé', 'Forte croissance, volatilité accepté', 'Élevé (15%+)', 'Long terme (5+ ans)');
""")

# TABLE CONTRATS
cursor.execute("""
CREATE TABLE IF NOT EXISTS contrats (
    numero INT AUTO_INCREMENT,
    type_compte VARCHAR(25),
    nombre_annees INT NOT NULL,
    taux_interet INT NOT NULL,
    beneficiaires VARCHAR(60),
    mont_initial INT NOT NULL,
    mont_mensuel INT NOT NULL,
    nas_client CHAR(9) NOT NULL,
    id_risque INT,
    PRIMARY KEY(numero),
    CONSTRAINT Fk_nasclient_nas FOREIGN KEY (nas_client) REFERENCES clients(nas) ON DELETE CASCADE,
    CONSTRAINT Fk_idrisque_id FOREIGN KEY (id_risque) REFERENCES risques(id)
);
""")

# Admin par défaut
username = "admin"
email = "admin@admin.com"
password = generate_password_hash("Admin123")
role = "admin"

cursor.execute("""
INSERT INTO users (username, email, password, role)
VALUES (%s, %s, %s, %s)
""", (username, email, password, role))

user_id = cursor.lastrowid
cursor.execute("""
INSERT INTO admin (nom, prenom, id_user, sexe, poste, nas, langue, adresse)
VALUES ('Admin_nom', 'Admin_prenom', %s, 'Homme', 'Administrateur', '123456789', 'Français', 'Adresse admin')
""", (user_id,))



cursor.execute("DROP PROCEDURE IF EXISTS insert_user_si_username_mail_unique")
cursor.execute("""
CREATE PROCEDURE insert_user_si_username_mail_unique(
  IN p_username VARCHAR(50),
  IN p_email VARCHAR(100),
  IN p_password VARCHAR(255),
  IN p_role VARCHAR(10),
  OUT p_user_id INT
)
BEGIN
  DECLARE nb INT DEFAULT 0;

  SELECT COUNT(*) INTO nb FROM users WHERE username = p_username;
  IF nb > 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Nom d''utilisateur déjà utilisé.';
  END IF;

  SELECT COUNT(*) INTO nb FROM users WHERE email = p_email;
  IF nb > 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Email déjà utilisé.';
  END IF;

  SELECT COUNT(*) INTO nb FROM clients WHERE mail = p_email;
  IF nb > 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Email déjà utilisé.';
  END IF;

  INSERT INTO users (username, email, password, role)
  VALUES (p_username, p_email, p_password, p_role);
  SET p_user_id = LAST_INSERT_ID();
END
""")


# PROCEDURE : Vérifier NAS unique pour conseiller
cursor.execute("DROP PROCEDURE IF EXISTS insert_conseiller_si_nas_unique")
cursor.execute("""
CREATE PROCEDURE insert_conseiller_si_nas_unique(
  IN p_user_id INT,
  IN p_nom VARCHAR(25),
  IN p_prenom VARCHAR(25),
  IN p_annee_activite INT,
  IN p_numero_permis INT,
  IN p_sexe VARCHAR(15),
  IN p_langue VARCHAR(50),
  IN p_type_permis VARCHAR(35),
  IN p_salaire INT,
  IN p_nas CHAR(9),
  IN p_adresse VARCHAR(50)
)
BEGIN
    DECLARE nb INT DEFAULT 0;

    SELECT COUNT(*) INTO nb FROM conseillers WHERE nas = p_nas;
    IF nb > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Le NAS est déjà utilisé.';
    END IF;
    
    SELECT COUNT(*) INTO nb FROM clients WHERE nas = p_nas;
    IF nb > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Le NAS est déjà utilisé.';
    END IF;

    SELECT COUNT(*) INTO nb FROM admin WHERE nas = p_nas;
    IF nb > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Le NAS est déjà utilisé.';
    END IF;
               
    INSERT INTO conseillers (
        id_user, nom, prenom, annee_activite, numero_permis, sexe,
        langue, type_permis, salaire, nas, adresse
        )
        VALUES (
        p_user_id, p_nom, p_prenom, p_annee_activite, p_numero_permis, p_sexe,
        p_langue, p_type_permis, p_salaire, p_nas, p_adresse
);

END
""")


cursor.execute("DROP PROCEDURE IF EXISTS verifier_nas_client_contrat")

cursor.execute("""
CREATE PROCEDURE verifier_nas_client_contrat(
    IN nas_c CHAR(9),
    IN tab VARCHAR(25),
    IN id_ INT
)
BEGIN
    DECLARE nb INT;

    IF tab = 'clients' THEN
        SELECT COUNT(*) INTO nb FROM clients WHERE nas = nas_c;
        IF (nb > 0) THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'NAS existant';
        END IF;

        SELECT COUNT(*) INTO nb FROM conseillers WHERE nas = nas_c;
        IF (nb > 0) THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Un conseiller ne peut pas etre un client';
        END IF;
               
        SELECT COUNT(*) INTO nb FROM admin WHERE nas = nas_c;
        IF (nb > 0) THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Un Admin ne peut pas etre un client';
        END IF;


    ELSEIF tab = 'contrats' THEN
        SELECT COUNT(*) INTO nb
        FROM clients cl
        INNER JOIN conseillers con ON cl.id_conseiller = con.id
        WHERE cl.nas = nas_c AND con.id = id_;
        
        IF (nb = 0) THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'NAS client inexistant ou pas parmi vos clients';
        END IF;
    END IF;
END
""")

cursor.execute("DROP PROCEDURE IF EXISTS verifier_mail_client")
cursor.execute("""
CREATE PROCEDURE verifier_mail_client(IN mail VARCHAR(50))
BEGIN
    DECLARE nb INT;
    SELECT COUNT(*) INTO nb FROM users WHERE email = mail;
    IF nb > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Adresse courriel déjà utilisée';
    END IF;
END
""")


# TRIGGERS : mise à jour du nombre de clients
cursor.execute("DROP TRIGGER IF EXISTS after_client_insert")
cursor.execute("""
CREATE TRIGGER after_client_insert
AFTER INSERT ON clients
FOR EACH ROW
BEGIN
    UPDATE conseillers
    SET nombre_clients = nombre_clients + 1
    WHERE id = NEW.id_conseiller;
END;
""")

cursor.execute("DROP TRIGGER IF EXISTS after_client_delete")
cursor.execute("""
CREATE TRIGGER after_client_delete
AFTER DELETE ON clients
FOR EACH ROW
BEGIN
    UPDATE conseillers
    SET nombre_clients = nombre_clients - 1
    WHERE id = OLD.id_conseiller;
END;
""")


# INDEX pour accélerer les recherches : pas besoin pour nas et numeros permis car c automatiquement cree par mysql 
# ce sont des clé Unique

cursor.execute("CREATE INDEX index_conseillers_nom ON conseillers(nom);")
cursor.execute("CREATE INDEX index_clients_nom ON clients(nom);")



print("Base de données, tables, procédures et triggers créés avec succès.")
cursor.close()
connection.close()
