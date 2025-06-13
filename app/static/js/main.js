// Função para preview da imagem
function previewImage(input) {
    const preview = document.getElementById('preview');
    const fileName = document.getElementById('fileName');
    const imagePreview = document.getElementById('imagePreview');
    
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        
        reader.onload = function(e) {
            preview.src = e.target.result;
            imagePreview.classList.remove('hidden');
        }
        
        reader.readAsDataURL(input.files[0]);
        fileName.textContent = input.files[0].name;
    }
}

// Manipulação do formulário
document.getElementById('crachaForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    // Elementos da UI
    const loading = document.getElementById('loading');
    const success = document.getElementById('success');
    const error = document.getElementById('error');
    const errorMessage = document.getElementById('errorMessage');
    const downloadLink = document.getElementById('downloadLink');
    
    // Esconder mensagens anteriores
    success.classList.add('hidden');
    error.classList.add('hidden');
    
    // Mostrar loading
    loading.classList.remove('hidden');
    
    try {
        // Criar FormData
        const formData = new FormData();
        formData.append('nome', document.getElementById('nome').value);
        formData.append('instituicao', document.getElementById('instituicao').value);
        formData.append('rg', document.getElementById('rg').value);
        formData.append('matricula', document.getElementById('matricula').value);
        formData.append('modalidade', document.getElementById('modalidade').value);
        formData.append('foto', document.getElementById('foto').files[0]);
        
        // Enviar requisição
        const response = await fetch('/api/gerar-cracha', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('Erro ao gerar crachá');
        }
        
        // Obter o blob do PDF
        const blob = await response.blob();
        
        // Criar URL para download
        const url = window.URL.createObjectURL(blob);
        
        // Configurar link de download
        downloadLink.href = url;
        downloadLink.download = `cracha_${document.getElementById('matricula').value}.pdf`;
        
        // Mostrar mensagem de sucesso
        success.classList.remove('hidden');
        
    } catch (err) {
        // Mostrar mensagem de erro
        errorMessage.textContent = err.message;
        error.classList.remove('hidden');
    } finally {
        // Esconder loading
        loading.classList.add('hidden');
    }
});

// Validação do formulário
document.querySelectorAll('input, select').forEach(input => {
    input.addEventListener('invalid', function(e) {
        e.preventDefault();
        this.classList.add('border-red-500');
    });
    
    input.addEventListener('input', function() {
        this.classList.remove('border-red-500');
    });
}); 