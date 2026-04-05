<!DOCTYPE html>
<html lang="uz" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Aqlli Lug'at</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        body { background-color: #111827; color: #f3f4f6; }
        .drag-over { border-color: #3b82f6 !important; background-color: rgba(59, 130, 246, 0.1) !important; }
        .word-card { transition: all 0.2s ease-in-out; }
        .word-card:active { transform: scale(0.95); }
        .fade-out { opacity: 0; transform: scale(0.8); pointer-events: none; }
        .loader { border-top-color: #3b82f6; animation: spin 1s linear infinite; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        /* Flashcard animatsiyasi */
        .flashcard-inner { transition: transform 0.6s; transform-style: preserve-3d; }
        .is-flipped { transform: rotateX(180deg); }
        .flashcard-front, .flashcard-back { backface-visibility: hidden; position: absolute; top: 0; left: 0; width: 100%; height: 100%; }
        .flashcard-back { transform: rotateX(180deg); }
    </style>
</head>
<body class="min-h-screen flex flex-col items-center py-10 px-4">

    <div id="main-view" class="w-full max-w-4xl bg-gray-800 rounded-2xl shadow-2xl p-6 md:p-8">
        <div class="text-center mb-8">
            <h1 class="text-3xl font-extrabold text-blue-400 mb-2"><i class="fa-solid fa-camera mr-2"></i>AI Aqlli Lug'at</h1>
            <p class="text-gray-400 text-sm">Rasmni yuklang, men uni so'zlarga ajrataman. Bilgan so'zlaringizni bosib o'chiring!</p>
        </div>

        <div id="dropZone" class="relative border-2 border-dashed border-gray-600 bg-gray-700/50 hover:bg-gray-700 rounded-xl h-64 flex flex-col items-center justify-center cursor-pointer transition-colors mb-6 group">
            <input type="file" id="fileInput" accept="image/*" class="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10">
            <div id="uploadText" class="text-center pointer-events-none">
                <i class="fa-solid fa-cloud-arrow-up text-5xl text-gray-400 group-hover:text-blue-400 transition-colors mb-3"></i>
                <p class="text-lg font-medium text-gray-300">Rasmni shu yerga tashlang</p>
                <p class="text-sm text-gray-500 mt-1">yoki tanlash uchun bosing</p>
            </div>
            <img id="imagePreview" class="absolute inset-0 w-full h-full object-contain hidden p-2 rounded-xl" alt="Preview">
        </div>

        <button id="scanBtn" onclick="processImage()" class="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 px-4 rounded-xl shadow-lg transition-colors flex justify-center items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed">
            <i class="fa-solid fa-bolt"></i> Skaner qilish
        </button>

        <div id="loading" class="hidden mt-6 flex flex-col items-center justify-center bg-gray-700/30 p-6 rounded-xl border border-gray-600">
            <div class="loader ease-linear rounded-full border-4 border-t-4 border-gray-500 h-12 w-12 mb-4"></div>
            <p class="text-blue-400 font-medium animate-pulse text-center">AI matnni o'qimoqda...<br><span class="text-xs text-gray-400">(Bepul model bo'lgani uchun 10-15 soniya vaqt olishi mumkin)</span></p>
        </div>

        <div id="resultsArea" class="hidden mt-10">
            <div class="flex justify-between items-center mb-4 border-b border-gray-600 pb-2">
                <h2 class="text-xl font-bold text-gray-200">Ajratilgan So'zlar</h2>
                <button onclick="startPractice()" class="bg-green-600 hover:bg-green-500 text-white px-4 py-2 rounded-lg text-sm font-bold shadow transition-colors">
                    <i class="fa-solid fa-dumbbell mr-1"></i> Mashq qilish
                </button>
            </div>
            <p class="text-xs text-yellow-400 mb-4"><i class="fa-solid fa-circle-info"></i> Bilgan so'zingizni ustiga bosib o'chiring. Qolganlarini mashq qilamiz!</p>
            
            <div id="wordsGrid" class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                </div>
        </div>
    </div>

    <div id="practice-view" class="hidden w-full max-w-2xl bg-gray-800 rounded-2xl shadow-2xl p-6 md:p-10 text-center">
        <h2 class="text-2xl font-bold text-green-400 mb-6"><i class="fa-solid fa-brain mr-2"></i>Yodlash Mashqi</h2>
        
        <p id="progressText" class="text-gray-400 mb-4 text-sm font-medium">1 / 10</p>

        <div class="perspective-1000 w-full h-64 mx-auto cursor-pointer mb-8" onclick="flipCard()">
            <div id="flashcardInner" class="flashcard-inner w-full h-full relative">
                <div class="flashcard-front bg-gray-700 border-2 border-gray-600 rounded-2xl flex flex-col items-center justify-center shadow-lg absolute">
                    <p class="text-gray-400 text-sm absolute top-4">Tarjimasini ko'rish uchun bosing</p>
                    <h3 id="cardEn" class="text-4xl font-extrabold text-white text-center px-4 break-words">Word</h3>
                </div>
                <div class="flashcard-back bg-blue-900 border-2 border-blue-500 rounded-2xl flex flex-col items-center justify-center shadow-lg absolute">
                    <p class="text-blue-300 text-sm absolute top-4">Inglizchasiga qaytish uchun bosing</p>
                    <h3 id="cardUz" class="text-3xl font-bold text-white text-center px-4 break-words">Tarjima</h3>
                </div>
            </div>
        </div>

        <div class="flex justify-center gap-4">
            <button onclick="endPractice()" class="bg-gray-600 hover:bg-gray-500 text-white px-6 py-3 rounded-xl font-medium transition-colors">Tugatish</button>
            <button onclick="nextCard()" class="bg-green-600 hover:bg-green-500 text-white px-8 py-3 rounded-xl font-bold text-lg shadow-lg transition-colors">Keyingisi <i class="fa-solid fa-arrow-right ml-1"></i></button>
        </div>
    </div>

    <script>
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('fileInput');
        const imagePreview = document.getElementById('imagePreview');
        const uploadText = document.getElementById('uploadText');
        const resultsArea = document.getElementById('resultsArea');
        const wordsGrid = document.getElementById('wordsGrid');
        
        let currentWords = [];
        let currentIndex = 0;

        // Drag & Drop animatsiyalari
        dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('drag-over'); });
        dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('drag-over');
            if (e.dataTransfer.files.length) {
                fileInput.files = e.dataTransfer.files;
                showPreview(fileInput.files[0]);
            }
        });

        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length) showPreview(e.target.files[0]);
        });

        function showPreview(file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                imagePreview.src = e.target.result;
                imagePreview.classList.remove('hidden');
                uploadText.classList.add('hidden');
            };
            reader.readAsDataURL(file);
        }

        async function processImage() {
            if (!fileInput.files.length) return alert("Iltimos, avval rasm yuklang!");

            const scanBtn = document.getElementById('scanBtn');
            const loading = document.getElementById('loading');
            
            scanBtn.disabled = true;
            loading.classList.remove('hidden');
            resultsArea.classList.add('hidden');
            wordsGrid.innerHTML = '';
            currentWords = [];

            const formData = new FormData();
            formData.append("file", fileInput.files[0]);

            try {
                // To'g'ridan-to'g'ri orqa fonga so'rov yuborish (Boshqa oyna ochilmaydi!)
                const response = await fetch('/upload/', { method: 'POST', body: formData });
                const data = await response.json();

                if (data.error) {
                    alert("Xato: " + data.error + "\n" + data.details);
                } else {
                    currentWords = [...(data.words || []), ...(data.idioms || [])];
                    renderWords();
                    resultsArea.classList.remove('hidden');
                }
            } catch (err) {
                alert("Server xatosi. Iltimos tekshiring.");
            } finally {
                scanBtn.disabled = false;
                loading.classList.add('hidden');
            }
        }

        function renderWords() {
            wordsGrid.innerHTML = '';
            if (currentWords.length === 0) {
                wordsGrid.innerHTML = '<p class="text-gray-400 col-span-full text-center">Hamma so\'zlarni o\'chirib bo\'ldingiz!</p>';
                return;
            }

            currentWords.forEach((item, index) => {
                const div = document.createElement('div');
                div.className = "word-card bg-gray-700 border border-gray-600 p-4 rounded-xl cursor-pointer hover:bg-red-900/40 hover:border-red-500/50 flex flex-col justify-center items-center text-center relative overflow-hidden group";
                
                // Ustiga borganda chiqadigan Qizil X belgisi
                div.innerHTML = `
                    <div class="absolute inset-0 bg-red-500/20 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                        <i class="fa-solid fa-trash-can text-red-400 text-3xl"></i>
                    </div>
                    <span class="font-bold text-lg text-white group-hover:opacity-10">${item.en}</span>
                    <span class="text-sm text-blue-300 mt-1 group-hover:opacity-10">${item.uz}</span>
                `;

                // Bosganda o'chirish logikasi
                div.onclick = function() {
                    div.classList.add('fade-out');
                    setTimeout(() => {
                        currentWords = currentWords.filter(w => w.en !== item.en);
                        renderWords();
                    }, 200);
                };

                wordsGrid.appendChild(div);
            });
        }

        // ---- MASHQ QILISH (Flashcard) LOGIKASI ----
        function startPractice() {
            if (currentWords.length === 0) return alert("Mashq qilish uchun so'z qolmadi!");
            document.getElementById('main-view').classList.add('hidden');
            document.getElementById('practice-view').classList.remove('hidden');
            currentIndex = 0;
            updateCard();
        }

        function endPractice() {
            document.getElementById('practice-view').classList.add('hidden');
            document.getElementById('main-view').classList.remove('hidden');
            document.getElementById('flashcardInner').classList.remove('is-flipped');
        }

        function updateCard() {
            document.getElementById('flashcardInner').classList.remove('is-flipped');
            document.getElementById('progressText').innerText = `${currentIndex + 1} / ${currentWords.length}`;
            document.getElementById('cardEn').innerText = currentWords[currentIndex].en;
            document.getElementById('cardUz').innerText = currentWords[currentIndex].uz;
        }

        function flipCard() {
            document.getElementById('flashcardInner').classList.toggle('is-flipped');
        }

        function nextCard() {
            currentIndex++;
            if (currentIndex >= currentWords.length) {
                alert("Mashq tugadi! Barakalla!");
                endPractice();
            } else {
                updateCard();
            }
        }
    </script>
</body>
</html>
