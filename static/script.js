

// Fonction de validation du NAS
function validateNas(nas) {
    // Vérifie que le NAS est soit 9 chiffres sans espaces XXXXXXXXX, ou  au format XXX XXX XXX
    const regex = /^(?:\d{9}|\d{3} \d{3} \d{3})$/;
    return regex.test(nas);
  }
  
  // Verifier puis affichier l'erreur d'entrée
  document.addEventListener("DOMContentLoaded", function() {
    const form = document.getElementById('create_Conseiller');
    if (form) {
      form.addEventListener('submit', function(e) {
        const nasInput = document.getElementById('nasInputcons');
        if (nasInput && !validateNas(nasInput.value)) {
          e.preventDefault();
          alert('Le NAS doit être composé de 9 chiffres, soit sous la forme "123456789" ou "123 456 789".');
        }
      });
    }
  });



  document.addEventListener("DOMContentLoaded", function() {
    const form = document.getElementById('formAjoutClient');
    if (form) {
      form.addEventListener('submit', function(e) {
        const nasInput = document.getElementById('nasInputClient');
        if (nasInput && !validateNas(nasInput.value)) {
          e.preventDefault();
          alert('Le NAS doit être composé de 9 chiffres, soit sous la forme "123456789" ou "123 456 789".');
        }
      });
    }
  });





  document.addEventListener("DOMContentLoaded", function() {
    const form = document.getElementById('formAjoutContrat');
    if (form) {
      form.addEventListener('submit', function(e) {
        const nasInput = document.getElementById('nasInputContrat');
        if (nasInput && !validateNas(nasInput.value)) {
          e.preventDefault();
          alert('Le NAS doit être composé de 9 chiffres, soit sous la forme "123456789" ou "123 456 789".');
        }
      });
    }
  });
  
  

  document.addEventListener("DOMContentLoaded", function () {
    const form = document.querySelector("form");
    if (form) {
        form.addEventListener("submit", function (e) {
            const nasInput = document.getElementById("nasInput");
            if (nasInput && !validateNas(nasInput.value)) {
                e.preventDefault();
                alert("Le NAS doit être composé de 9 chiffres (ex : 123456789 ou 123 456 789).");
            }
        });
    }
});
  

// Validation mot de passe 
  function validatePassword(pwd) {
    const regex = /^(?=.*[A-Z])(?=.*\d).{7,}$/;
    return regex.test(pwd);
  }
  

  document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("admin_edit_password");
    if (form) {
      form.addEventListener("submit", function (e) {
        const password = document.querySelector('input[name="password"]').value;
        if (!validatePassword(password)) {
          e.preventDefault();
          alert("Mot de passe non sécuritaire : min 7 caractères, au moins 1 majuscule et 1 chiffre.");
        }
      });
    }
  });
  

  document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("create_Conseiller");
    if (form) {
      form.addEventListener("submit", function (e) {
        const password = document.querySelector('input[name="password"]').value;
        if (!validatePassword(password)) {
          e.preventDefault();
          alert("Mot de passe non sécuritaire : min 7 caractères, au moins 1 majuscule et 1 chiffre.");
        }
      });
    }
  });


  document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("conseiller_edit_connexion");
    if (form) {
      form.addEventListener("submit", function (e) {
        const password = document.querySelector('input[name="password"]').value;
        if (!validatePassword(password)) {
          e.preventDefault();
          alert("Mot de passe non sécuritaire : min 7 caractères, au moins 1 majuscule et 1 chiffre.");
        }
      });
    }
  });
  