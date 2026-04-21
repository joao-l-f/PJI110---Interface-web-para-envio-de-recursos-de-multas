document.addEventListener("DOMContentLoaded", () => {

  // ==============================
  // ESTRUTURA LÓGICA DA EXIBIÇÃO DO CARD INFORMATIVO
  // ==============================

  const radios = document.querySelectorAll('input[name="tipo"]');
  const container = document.querySelector('.card-right');
  const docs = Array.from(document.querySelectorAll('.doc-item'));

  const relacao = {
    0: ["Notificação de autuação","CRLV","CNH (Proprietário)","CNH (Condutor indicado)"],
    1: ["Notificação de autuação","CRLV","CNH (Proprietário)","Certidão de pontos"],
    2: ["Notificação de autuação","CRLV","CNH (Requerente do Recurso)","Documentos que comprovem a defesa"],
    3: ["Notificação de autuação","CRLV","CNH (Requerente do Recurso)","Documentos que comprovem a defesa"],
    4: ["Notificação de autuação","CRLV","CNH (Requerente do Recurso)"]
  };

  function atualizarLista(index) {
    const necessarios = relacao[index];
    let ativos = [];
    let inativos = [];

    docs.forEach(doc => {
      const titulo = doc.querySelector("strong").innerText.trim();

      if (necessarios.includes(titulo)) {
        doc.style.opacity = "1";
        ativos.push(doc);
      } else {
        doc.style.opacity = "0.3";
        inativos.push(doc);
      }
    });

    const titulo = container.querySelector("h2");
    container.innerHTML = "";
    container.appendChild(titulo);

    ativos.forEach(el => container.appendChild(el));
    inativos.forEach(el => container.appendChild(el));
  }

  docs.forEach(doc => doc.style.opacity = "0.3");

  radios.forEach((radio, index) => {
    radio.addEventListener("change", () => atualizarLista(index));
  });

  // ==============================
  // ESTRUTURA LÓGICA DA EXIBIÇÃO DOS ANEXOS
  // ==============================

  const form = document.getElementById("formulario");
  const radiosTipo = document.querySelectorAll("input[name='tipo']");
  const radiosReq = document.querySelectorAll("input[name='requerente']");
  const uploads = document.querySelectorAll(".upload");

  const regras = {
    indicacao: {
      any: ["Notificação de Autuação","CRLV","CNH Proprietário","CNH do Condutor"]
    },
    advertencia: {
      proprietario: ["Notificação de Autuação","CRLV","CNH Proprietário","Certidão de Pontos"],
      condutor: ["Notificação de Autuação","CRLV","CNH do Condutor","Certidão de Pontos"],
      representante: ["Notificação de Autuação","CRLV","CNH do Condutor","Certidão de Pontos"]
    },
    defesa: {
      proprietario: ["Notificação de Autuação","CRLV","CNH Proprietário","Provas de Defesa"],
      condutor: ["Notificação de Autuação","CRLV","CNH do Condutor","Provas de Defesa"],
      representante: ["Notificação de Autuação","CRLV","CNH do Condutor","Provas de Defesa"]
    },
    recurso_1ªinstancia: {
      proprietario: ["Notificação de Autuação","CRLV","CNH Proprietário","Provas de Defesa"],
      condutor: ["Notificação de Autuação","CRLV","CNH do Condutor","Provas de Defesa"],
      representante: ["Notificação de Autuação","CRLV","CNH do Condutor","Provas de Defesa"]
    },
    recurso_2ªinstancia: {
      proprietario: ["Notificação de Autuação","CRLV","CNH Proprietário"],
      condutor: ["Notificação de Autuação","CRLV","CNH do Condutor"],
      representante: ["Notificação de Autuação","CRLV","CNH do Condutor"]
    }
  };

  function getSelecionado(name) {
    const el = document.querySelector(`input[name='${name}']:checked`);
    return el ? el.value : null;
  }

  function resetUploads() {
    uploads.forEach(upload => {
      upload.style.display = "none";
      const input = upload.querySelector("input[type='file']");
      input.required = false;
    });
  }

  function aplicarRegras() {
    const tipo = getSelecionado("tipo");
    const req = getSelecionado("requerente");

    resetUploads();

    if (!tipo || !req) {
      form.classList.add("form-disabled");
      return;
    }

    form.classList.remove("form-disabled");

    let lista = tipo === "indicacao"
      ? regras.indicacao.any
      : regras[tipo][req];

    uploads.forEach(upload => {
      const nome = upload.querySelector("span").innerText.trim();

      if (lista.includes(nome)) {
        upload.style.display = "flex";
        upload.querySelector("input").required = true;
      }
    });
  }

  radiosTipo.forEach(r => r.addEventListener("change", aplicarRegras));
  radiosReq.forEach(r => r.addEventListener("change", aplicarRegras));

  form.classList.add("form-disabled");
  resetUploads();

  // ==============================
  // CAMPOS OCULTOS DE IDENTIFICAÇÃO DO REQUERENTE, PARA ENVIO AO E-MAIL
  // ==============================

  function atualizarHidden() {
    const tipo = document.querySelector('input[name="tipo"]:checked');
    const req = document.querySelector('input[name="requerente"]:checked');

    document.getElementById("tipoHidden").value = tipo ? tipo.value : "";
    document.getElementById("requerenteHidden").value = req ? req.value : "";
  }

  radiosTipo.forEach(r => r.addEventListener("change", atualizarHidden));
  radiosReq.forEach(r => r.addEventListener("change", atualizarHidden));

// ==============================
// INTERFACE DE UPLOAD
// ==============================

document.querySelectorAll(".upload").forEach(container => {
  const input = container.querySelector("input[type=file]");
  const span = container.querySelector("span");
  const button = container.querySelector("button");

  if (!input) return; // segurança

  // Clique no botão abre o input
  if (button) {
    button.addEventListener("click", (e) => {
      e.preventDefault();
      input.click();
    });
  }

  // Mudança de arquivo
  input.addEventListener("change", () => {

    if (input.files && input.files.length > 0) {
      container.classList.add("active");

      // Nome do arquivo (ou quantidade)
      if (input.files.length === 1) {
        if (span) span.textContent = input.files[0].name;
      } else {
        if (span) span.textContent = `${input.files.length} arquivos selecionados`;
      }

      if (button) button.textContent = "Arquivo anexado ✔";

    } else {
      container.classList.remove("active");

      if (span) span.textContent = "Nenhum arquivo";
      if (button) button.textContent = "Selecionar arquivo";
    }

  });
});

  // ==============================
  // ENVIO E VALIDAÇÃO DOS CAMPOS OBRIGATÓRIOS
  // ==============================

  form.addEventListener("submit", function (e) {

    let valido = true;

    const inputs = form.querySelectorAll("input[required], textarea[required], select[required]");
    inputs.forEach(input => {
      if (!input.value || input.value.trim() === "") {
        valido = false;
        input.style.border = "2px solid red";
      } else {
        input.style.border = "";
      }
    });

    const arquivos = form.querySelectorAll("input[type='file']");
    arquivos.forEach(file => {
      if (file.required && file.files.length === 0) {
        valido = false;
        file.parentElement.style.border = "2px solid red";
      } else {
        file.parentElement.style.border = "";
      }
    });

    const checkbox = form.querySelector("input[type='checkbox']");
    if (!checkbox.checked) {
      valido = false;
      alert("Você deve aceitar o termo antes de enviar.");
    }

    const emailInput = form.querySelector("input[name='email']");
    const email = emailInput.value.trim();

    if (!email || !emailValido(email)) {
      e.preventDefault();
      emailInput.style.border = "2px solid red";
      mostrarErroEmail();
      return;
    }

    if (!valido) {
      e.preventDefault();
      alert("Preencha todos os campos obrigatórios.");
      return;
    }

    // MOSTRA POPUP E ENVIA
    e.preventDefault();
    mostrarPopup();

    setTimeout(() => {
      form.submit();
    }, 1500);
  });

});

// ==============================
// VALIDAÇÃO EMAIL
// ==============================

function emailValido(email) {
  const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return regex.test(email);
}

// ==============================
// MENSAGEM DE ENVIO
// ==============================

function mostrarPopup() {
  const popup = document.createElement("div");

  popup.innerHTML = `
    <div style="position:fixed;top:0;left:0;width:100%;height:100%;
    background:rgba(0,0,0,0.6);display:flex;align-items:center;justify-content:center;z-index:9999;">
      
      <div style="background:white;padding:30px;border-radius:10px;text-align:center;">
        <h2 style="color:green;">✔ Envio realizado!</h2>
        <p>Seu formulário foi enviado com sucesso.</p>
      </div>
    </div>
  `;

  document.body.appendChild(popup);
}

// ==============================
// MENSAGEM DE ERRO
// ==============================

function mostrarErroEmail() {
  const popup = document.createElement("div");

  popup.innerHTML = `
    <div style="position:fixed;top:0;left:0;width:100%;height:100%;
    background:rgba(0,0,0,0.6);display:flex;align-items:center;justify-content:center;z-index:9999;">
      
      <div style="background:white;padding:30px;border-radius:10px;text-align:center;">
        <h2 style="color:red;">❌ E-mail inválido</h2>
        <p>Por favor, insira um endereço válido.</p>

        <button onclick="this.closest('div').parentElement.remove()" 
        style="margin-top:15px;padding:10px 20px;border:none;background:#075B96;color:white;border-radius:5px;cursor:pointer;">
          OK
        </button>
      </div>
    </div>
  `;

  document.body.appendChild(popup);
}


// ==============================
// ÍCONE INFORMATIVO - PÁGINA DE BUSCA
// ==============================

document.querySelectorAll(".input-icon").forEach(container => {
  const icon = container.querySelector("i");
  const tooltip = container.querySelector(".tooltip");

  icon.addEventListener("click", (e) => {
    e.stopPropagation();
    tooltip.classList.toggle("active");
  });

  document.addEventListener("click", () => {
    tooltip.classList.remove("active");
  });
});

// ==============================
// BOTÃO PARA IMPRIMIR PROTOCOLO
// ==============================

document.addEventListener("DOMContentLoaded", () => {
    const botao = document.getElementById("print");

    if (botao) {
        botao.addEventListener("click", () => {
            window.print();
        });
    }
});

