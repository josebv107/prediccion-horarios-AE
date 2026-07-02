document.addEventListener('DOMContentLoaded', () => {
    // Referencias a elementos del DOM - Autenticación y Dashboard
    const loginView = document.getElementById('login-view');
    const dashboardView = document.getElementById('dashboard-view');
    const loginForm = document.getElementById('login-form');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const loginError = document.getElementById('login-error');
    const errorMessage = document.getElementById('error-message');
    
    const btnHome = document.getElementById('btn-home');
    const btnLogout = document.getElementById('btn-logout');
    const studentBar = document.getElementById('student-bar');
    const studentBarText = document.getElementById('student-bar-text');
    
    const profileName = document.getElementById('profile-name');
    const profileId = document.getElementById('profile-id');
    const cardHorario = document.getElementById('card-horario');

    // Referencias a elementos del DOM - Matrícula (Actualizado con Panel Dividido)
    const matriculaView = document.getElementById('matricula-view');
    const coursesSidebar = document.getElementById('courses-sidebar');
    const courseDetailsPanel = document.getElementById('course-details-panel');
    const conflictAlert = document.getElementById('conflict-alert');
    const conflictMessage = document.getElementById('conflict-message');
    const matriculaCreditsText = document.getElementById('matricula-credits');
    const btnConfirmEnroll = document.getElementById('btn-confirm-enroll');
    const timetableGrid = document.querySelector('.timetable-grid');
    const enrollSuccessModal = document.getElementById('enroll-success-modal');
    const btnModalClose = document.getElementById('btn-modal-close');

    // Referencias a elementos del DOM - Predictor
    const btnPredictAnalysis = document.getElementById('btn-predict-analysis');
    const predictView = document.getElementById('predict-view');
    const btnPredictBack = document.getElementById('btn-predict-back');
    
    // Elementos del Formulario y Resultados del Predictor
    const selectTrabaja = document.getElementById('predict-trabaja');
    const inputHorasTrabajo = document.getElementById('predict-horas-trabajo');
    const inputTraslado = document.getElementById('predict-traslado');
    const formPredictor = document.getElementById('predictor-form');
    const predictPlaceholder = document.getElementById('predict-placeholder');
    const predictResultsContent = document.getElementById('predict-results-content');
    const predictClassBadge = document.getElementById('predict-class-badge');
    const probBarsList = document.getElementById('prob-bars-list');
    const featCreditos = document.getElementById('feat-creditos');
    const featDias = document.getElementById('feat-dias');
    const featMuertas = document.getElementById('feat-muertas');
    const featExigencia = document.getElementById('feat-exigencia');
    const predictRecosList = document.getElementById('predict-recos-list');
    const modelAccuracy = document.getElementById('model-accuracy');
    const modelPrecision = document.getElementById('model-precision');
    const modelF1 = document.getElementById('model-f1');
    const cmMatrixBody = document.getElementById('cm-matrix-body');

    // Variables de Estado en el Cliente
    let currentStudent = null;
    let selectedSections = []; // Arreglo de objetos de sección
    let eligibleCourses = [];  // Asignaturas obtenidas de la base de datos
    let activeCourseId = null;  // Asignatura seleccionada actualmente en el menú lateral
    let initialEnrolledSectionIds = []; // IDs de matrícula al cargar para validar cambios

    // ══════════════════════════════════════════════
    // SESIÓN Y VISTAS DE ENTRADA
    // ══════════════════════════════════════════════
    const savedStudentCode = localStorage.getItem('student_code');
    if (savedStudentCode) {
        loadDashboard(savedStudentCode);
    } else {
        showLogin();
    }

    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = usernameInput.value.trim();
        const password = passwordInput.value;

        loginError.classList.add('hidden');
        const submitBtn = loginForm.querySelector('button[type="submit"]');
        submitBtn.disabled = true;
        submitBtn.textContent = 'Ingresando...';

        try {
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });
            const data = await response.json();

            if (response.ok && data.success) {
                localStorage.setItem('student_code', data.student.codigo);
                await loadDashboard(data.student.codigo);
            } else {
                showError(data.message || 'Código o contraseña incorrectos');
            }
        } catch (err) {
            console.error('Error al iniciar sesión:', err);
            showError('Error de conexión con el servidor. Inténtalo de nuevo.');
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Ingresar';
        }
    });

    btnLogout.addEventListener('click', () => {
        localStorage.removeItem('student_code');
        currentStudent = null;
        passwordInput.value = '';
        showLogin();
    });

    // Botón de Inicio en la barra de cabecera
    btnHome.addEventListener('click', () => {
        if (currentStudent) {
            loadDashboard(currentStudent.codigo);
        }
    });

    async function loadDashboard(codigo) {
        try {
            studentBarText.textContent = `Cargando datos del estudiante ${codigo}...`;
            const response = await fetch(`/api/student-info?codigo=${codigo}`);
            const data = await response.json();

            if (response.ok && data.success) {
                currentStudent = data.student;
                
                // Actualizar barra de información superior
                studentBarText.textContent = `${currentStudent.codigo} - ${currentStudent.apellidos.toUpperCase()} ${currentStudent.nombres.toUpperCase()}`;
                
                // Actualizar tarjeta de perfil
                profileName.textContent = `${currentStudent.apellidos}, ${currentStudent.nombres}`;
                profileId.textContent = `ID: ${currentStudent.codigo}`;
                
                // Mostrar Dashboard y ocultar otras vistas
                loginView.classList.add('hidden');
                matriculaView.classList.add('hidden');
                predictView.classList.add('hidden');
                dashboardView.classList.remove('hidden');
                
                studentBar.classList.remove('hidden');
                btnHome.classList.remove('hidden');
                btnLogout.classList.remove('hidden');
            } else {
                localStorage.removeItem('student_code');
                showLogin();
            }
        } catch (err) {
            console.error('Error cargando información de estudiante:', err);
            studentBarText.textContent = 'Error al cargar la información del estudiante';
            
            loginView.classList.add('hidden');
            matriculaView.classList.add('hidden');
            predictView.classList.add('hidden');
            dashboardView.classList.remove('hidden');
            
            studentBar.classList.remove('hidden');
            btnHome.classList.remove('hidden');
            btnLogout.classList.remove('hidden');
        }
    }

    function showLogin() {
        loginView.classList.remove('hidden');
        dashboardView.classList.add('hidden');
        matriculaView.classList.add('hidden');
        predictView.classList.add('hidden');
        
        studentBar.classList.add('hidden');
        btnHome.classList.add('hidden');
        btnLogout.classList.add('hidden');
    }

    function showError(message) {
        errorMessage.textContent = message;
        loginError.classList.remove('hidden');
    }

    // ══════════════════════════════════════════════
    // FLUJO DEL SIMULADOR DE MATRÍCULA
    // ══════════════════════════════════════════════
    if (cardHorario) {
        cardHorario.addEventListener('click', () => {
            if (currentStudent) {
                showMatricula();
            }
        });
    }

    // Navegación del Predictor de Aprobación
    if (btnPredictAnalysis) {
        btnPredictAnalysis.addEventListener('click', () => {
            matriculaView.classList.add('hidden');
            predictView.classList.remove('hidden');
            predictView.scrollIntoView({ behavior: 'smooth' });
        });
    }

    if (btnPredictBack) {
        btnPredictBack.addEventListener('click', () => {
            predictView.classList.add('hidden');
            matriculaView.classList.remove('hidden');
            matriculaView.scrollIntoView({ behavior: 'smooth' });
        });
    }

    function showMatricula() {
        dashboardView.classList.add('hidden');
        loginView.classList.add('hidden');
        matriculaView.classList.remove('hidden');
        
        selectedSections = [];
        conflictAlert.classList.add('hidden');
        
        // Resetear texto y estado del botón de confirmar
        btnConfirmEnroll.textContent = 'Confirmar Matrícula';
        
        // Renderizar fondo del calendario
        renderTimetableBackground();
        updateCreditsAndEnrollButton();
        
        // Cargar asignaturas elegibles
        loadEligibleCourses(currentStudent.codigo);
    }

    async function loadEligibleCourses(codigo) {
        try {
            coursesSidebar.innerHTML = '<p class="loading-placeholder" style="font-size: 10px; padding: 10px;">Cargando...</p>';
            courseDetailsPanel.innerHTML = '<div class="empty-details-placeholder">Selecciona una asignatura del catálogo de la izquierda para ver sus secciones disponibles.</div>';
            
            const response = await fetch(`/api/eligible-courses?codigo=${codigo}`);
            const data = await response.json();

            if (response.ok && data.courses) {
                eligibleCourses = data.courses;
                
                // 1. Precarga de Matrícula: Llenar el estado local con las secciones ya guardadas
                selectedSections = [];
                if (data.enrolled_section_ids && data.enrolled_section_ids.length > 0) {
                    data.enrolled_section_ids.forEach(secId => {
                        for (const curso of eligibleCourses) {
                            const foundSec = curso.secciones.find(s => s.id === secId);
                            if (foundSec) {
                                selectedSections.push({
                                    id: foundSec.id,
                                    nrc: foundSec.nrc,
                                    secc: foundSec.secc,
                                    tipo: foundSec.tipo,
                                    docente: foundSec.docente,
                                    horarios: foundSec.horarios,
                                    liga: foundSec.liga,
                                    cursoId: curso.id,
                                    cursoCodigo: curso.codigo,
                                    cursoNombre: curso.nombre,
                                    cursoCreditos: curso.creditos
                                });
                                break;
                            }
                        }
                    });
                }
                
                // Guardar los IDs de matrícula cargados inicialmente para validar cambios posteriores
                initialEnrolledSectionIds = data.enrolled_section_ids ? [...data.enrolled_section_ids] : [];
                
                // Seleccionar por defecto la primera asignatura
                if (eligibleCourses.length > 0) {
                    activeCourseId = eligibleCourses[0].id;
                } else {
                    activeCourseId = null;
                }
                
                renderCoursesSidebar();
                renderCourseDetails();
                drawTimetableBlocks();
                updateCreditsAndEnrollButton();
            } else {
                coursesSidebar.innerHTML = '<p class="loading-placeholder" style="font-size: 10px; padding: 10px; color: var(--canvas-red);">Error al cargar.</p>';
            }
        } catch (err) {
            console.error('Error al consultar asignaturas elegibles:', err);
            coursesSidebar.innerHTML = '<p class="loading-placeholder" style="font-size: 10px; padding: 10px; color: var(--canvas-red);">Error de red.</p>';
        }
    }

    // Comprobar estado de completitud de una asignatura (empty / incomplete / complete)
    function getCourseCompletionStatus(course) {
        const availableTypes = new Set(course.secciones.map(s => s.tipo));
        const selectedForCourse = selectedSections.filter(s => s.cursoId === course.id);
        
        if (selectedForCourse.length === 0) return 'empty';
        
        const selectedTypes = new Set(selectedForCourse.map(s => s.tipo));
        for (const type of availableTypes) {
            if (!selectedTypes.has(type)) {
                return 'incomplete';
            }
        }
        return 'complete';
    }

    // Dibujar el menú lateral de cursos (Sidebar)
    function renderCoursesSidebar() {
        coursesSidebar.innerHTML = '';
        
        if (eligibleCourses.length === 0) {
            coursesSidebar.innerHTML = '<p class="loading-placeholder" style="font-size: 10px; padding: 10px;">Catálogo vacío.</p>';
            return;
        }

        eligibleCourses.forEach(curso => {
            const btn = document.createElement('button');
            const isPending = curso.estado === 'pendiente';
            btn.className = `sidebar-course-btn ${isPending ? 'pending-deuda' : ''} ${activeCourseId === curso.id ? 'active' : ''}`;
            btn.setAttribute('data-id', curso.id);

            // Determinar tipo de punto indicador de estado
            const status = getCourseCompletionStatus(curso);
            let dotClass = 'course-status-dot';
            let dotTitle = 'No seleccionado';
            if (status === 'complete') {
                dotClass += ' complete';
                dotTitle = 'Asignatura totalmente matriculada';
            } else if (status === 'incomplete') {
                dotClass += ' incomplete';
                dotTitle = 'Faltan componentes (Teoría, Práctica o Lab)';
            }

            btn.innerHTML = `
                <span>${curso.codigo}</span>
                <span class="${dotClass}" title="${dotTitle}"></span>
            `;

            btn.addEventListener('click', () => {
                activeCourseId = curso.id;
                renderCoursesSidebar();
                renderCourseDetails();
            });

            coursesSidebar.appendChild(btn);
        });
    }

    // Dibujar los detalles y secciones del curso activo
    function renderCourseDetails() {
        courseDetailsPanel.innerHTML = '';

        if (!activeCourseId) {
            courseDetailsPanel.innerHTML = '<div class="empty-details-placeholder">Selecciona una asignatura del catálogo de la izquierda para ver sus secciones disponibles.</div>';
            return;
        }

        const curso = eligibleCourses.find(c => c.id === activeCourseId);
        if (!curso) return;

        // Header del detalle del curso
        const headerDiv = document.createElement('div');
        headerDiv.className = 'course-details-header';
        const isPending = curso.estado === 'pendiente';
        const badgeText = isPending ? `Ciclo ${curso.ciclo_malla} (Deuda)` : `Ciclo ${curso.ciclo_malla}`;
        
        headerDiv.innerHTML = `
            <h4>${curso.codigo} - ${curso.nombre}</h4>
            <p>Créditos: ${curso.creditos} | Periodo: ${badgeText}</p>
        `;
        courseDetailsPanel.appendChild(headerDiv);

        if (curso.secciones.length === 0) {
            const emptyP = document.createElement('p');
            emptyP.className = 'loading-placeholder';
            emptyP.textContent = 'No hay secciones disponibles para este periodo.';
            courseDetailsPanel.appendChild(emptyP);
            return;
        }

        // Determinar si ya hay secciones de este curso seleccionadas para ver el grupo/liga activo
        const courseSelections = selectedSections.filter(s => s.cursoId === curso.id);
        const activeLiga = courseSelections.length > 0 ? courseSelections[0].liga : null;

        // Renderizar las secciones disponibles
        curso.secciones.forEach(sec => {
            const isSelected = selectedSections.some(s => s.id === sec.id);
            // En modo simulación, todas las secciones están abiertas/libres para matrícula
            const isClosed = false;

            // Restricción de grupo (Liga): Si hay otra sección seleccionada y no coincide en grupo, se bloquea
            const isLigaLocked = activeLiga !== null && activeLiga !== sec.liga;

            const secElement = document.createElement('div');
            secElement.className = `section-item ${isSelected ? 'selected' : ''}`;

            const scheduleHtml = `
                <div class="section-schedule-pills">
                    ${sec.horarios.map(h => `
                        <div class="schedule-pill" title="Día">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
                            <span>${h.dia}</span>
                        </div>
                        <div class="schedule-pill" title="Horario">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                            <span>${h.hora_ini} - ${h.hora_fin}</span>
                        </div>
                        <div class="schedule-pill" title="Pabellón y Aula">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>
                            <span>${h.pabellon}-${h.aula || 'TBA'}</span>
                        </div>
                    `).join('')}
                </div>
            `;

            let buttonText = isSelected ? 'Quitar Asignación' : 'Añadir Sección';
            let buttonClass = isSelected ? 'btn-remove' : '';
            let buttonDisabled = '';

            if (!isSelected) {
                if (isLigaLocked) {
                    buttonText = `Bloqueado (Grupo ${activeLiga} activo)`;
                    buttonDisabled = 'disabled';
                } else if (isClosed) {
                    buttonText = 'Sección Cerrada';
                    buttonDisabled = 'disabled';
                }
            }

            secElement.innerHTML = `
                <div class="section-header-row">
                    <div>
                        <span class="section-name">Grupo ${sec.secc} (${sec.tipo === 'T' ? 'Teoría' : sec.tipo === 'P' ? 'Práctica' : 'Lab'})</span>
                        <span class="section-nrc">NRC: ${sec.nrc}</span>
                    </div>
                    <span class="section-slots">Vacantes: ${sec.capacidad - sec.matriculados}/${sec.capacidad}</span>
                </div>
                <div class="section-teacher">
                    <strong>Docente:</strong> ${sec.docente}
                    <span class="teacher-exigency-badge" title="Índice de Exigencia">
                        <svg viewBox="0 0 24 24" fill="currentColor" stroke="none"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>
                        <span>${sec.docente_exigencia.toFixed(1)}</span>
                    </span>
                </div>
                ${scheduleHtml}
                <button class="btn-add-section ${buttonClass}" ${buttonDisabled}>${buttonText}</button>
            `;

            const actionBtn = secElement.querySelector('.btn-add-section');
            actionBtn.addEventListener('click', () => {
                if (isSelected) {
                    removeSection(sec.id);
                } else {
                    addSection(sec, curso);
                }
            });

            courseDetailsPanel.appendChild(secElement);
        });
    }

    // ══════════════════════════════════════════════
    // GESTIÓN DE HORARIOS Y CONFLICTOS
    // ══════════════════════════════════════════════

    // Añadir una sección al horario del simulador
    function addSection(section, curso) {
        conflictAlert.classList.add('hidden');

        // 1. Validar cruce de horario (Solapamiento de tiempo)
        const conflict = checkScheduleConflict(section);
        if (conflict) {
            showConflictWarning(
                `El horario de <strong>${curso.nombre} (Grupo ${section.secc})</strong> se cruza con <strong>${conflict.cursoNombre} (Grupo ${conflict.secc})</strong> el día <strong>${conflict.dia}</strong> a las <strong>${conflict.timeRange}</strong>.`
            );
            return;
        }

        // 2. Validar límite de créditos
        const courseCredits = curso.creditos;
        const currentCredits = calculateTotalCredits();
        const isCourseAlreadyAdded = selectedSections.some(s => s.cursoId === curso.id);
        
        if (!isCourseAlreadyAdded && (currentCredits + courseCredits > 22)) {
            showConflictWarning('Has superado el límite permitido de 22 créditos para matrícula simulada.');
            return;
        }

        // 3. Validar restricción de liga (mismo grupo): Si ya hay otra sección, tiene que ser de la misma liga
        const courseSelections = selectedSections.filter(s => s.cursoId === curso.id);
        if (courseSelections.length > 0 && courseSelections[0].liga !== section.liga) {
            showConflictWarning(
                `No puedes mezclar grupos. Ya has seleccionado una sección de la <strong>Liga ${courseSelections[0].liga}</strong> para el curso <strong>${curso.nombre}</strong>. Debes seleccionar componentes del mismo grupo.`
            );
            return;
        }

        // Si ya tenía seleccionado otra sección del mismo tipo para el curso, removerla silenciosamente
        const sameTypeSection = selectedSections.find(s => s.cursoId === curso.id && s.tipo === section.tipo);
        if (sameTypeSection) {
            removeSection(sameTypeSection.id, true);
        }

        // Agregar sección a la lista
        selectedSections.push({
            id: section.id,
            nrc: section.nrc,
            secc: section.secc,
            tipo: section.tipo,
            docente: section.docente,
            horarios: section.horarios,
            liga: section.liga,
            cursoId: curso.id,
            cursoCodigo: curso.codigo,
            cursoNombre: curso.nombre,
            cursoCreditos: curso.creditos
        });

        // Re-renderizar
        renderCoursesSidebar();
        renderCourseDetails();
        drawTimetableBlocks();
        updateCreditsAndEnrollButton();
    }

    // Quitar una sección del horario
    function removeSection(secId, silent = false) {
        const secIndex = selectedSections.findIndex(s => s.id === secId);
        if (secIndex === -1) return;

        const removedSection = selectedSections[secIndex];
        selectedSections.splice(secIndex, 1);

        if (!silent) {
            renderCoursesSidebar();
            renderCourseDetails();
            drawTimetableBlocks();
            updateCreditsAndEnrollButton();
        }
    }

    // Comprobar si hay un solapamiento en el horario
    function checkScheduleConflict(newSection) {
        for (const selectedSec of selectedSections) {
            for (const newBlock of newSection.horarios) {
                for (const oldBlock of selectedSec.horarios) {
                    if (newBlock.dia === oldBlock.dia) {
                        const startNew = timeToMinutes(newBlock.hora_ini);
                        const endNew = timeToMinutes(newBlock.hora_fin);
                        const startOld = timeToMinutes(oldBlock.hora_ini);
                        const endOld = timeToMinutes(oldBlock.hora_fin);

                        if (startNew < endOld && startOld < endNew) {
                            return {
                                cursoNombre: selectedSec.cursoNombre,
                                secc: selectedSec.secc,
                                dia: newBlock.dia,
                                timeRange: `${oldBlock.hora_ini} - ${oldBlock.hora_fin}`
                            };
                        }
                    }
                }
            }
        }
        return null;
    }

    function timeToMinutes(timeStr) {
        const [h, m] = timeStr.split(':').map(Number);
        return h * 60 + m;
    }

    function showConflictWarning(htmlMessage) {
        conflictMessage.innerHTML = htmlMessage;
        conflictAlert.classList.remove('hidden');
        matriculaView.scrollIntoView({ behavior: 'smooth' });
    }

    function calculateTotalCredits() {
        const processedCourseIds = new Set();
        let credits = 0;
        selectedSections.forEach(sec => {
            if (!processedCourseIds.has(sec.cursoId)) {
                processedCourseIds.add(sec.cursoId);
                credits += sec.cursoCreditos;
            }
        });
        return credits;
    }

    function updateCreditsAndEnrollButton() {
        const totalCred = calculateTotalCredits();
        matriculaCreditsText.textContent = totalCred;
        
        // Habilitar confirmar si hay secciones seleccionadas
        btnConfirmEnroll.disabled = selectedSections.length === 0;
    }

    // ══════════════════════════════════════════════
    // DIBUJAR CALENDARIO SEMANAL (AJUSTADO HIJO DIRECTO GRID)
    // ══════════════════════════════════════════════

    // Dibujar celdas y labels de fondo en la rejilla principal
    function renderTimetableBackground() {
        // Remover elementos dinámicos previos (celdas y etiquetas) para no borrar cabeceras
        document.querySelectorAll('.timetable-grid > .time-cell, .timetable-grid > .grid-bg-cell').forEach(el => el.remove());
        
        // 1. Añadir etiquetas de hora en columna 1 (intervalos de 1 hora)
        for (let r = 2; r <= 17; r++) {
            const hour = (r - 2) + 7;
            const hourStr = `${hour.toString().padStart(2, '0')}`;
            
            const cell = document.createElement('div');
            cell.className = 'time-cell hour-line';
            cell.style.gridRow = r.toString();
            cell.style.gridColumn = '1';
            cell.textContent = hourStr;
            timetableGrid.appendChild(cell);
        }

        // 2. Añadir celdas de rejilla de fondo para los días (Lunes=2 a Sábado=7)
        for (let r = 2; r <= 17; r++) {
            for (let c = 2; c <= 7; c++) {
                const cell = document.createElement('div');
                cell.className = 'grid-bg-cell hour-line';
                if (c === 7) cell.classList.add('saturday-col');
                cell.style.gridRow = r.toString();
                cell.style.gridColumn = c.toString();
                timetableGrid.appendChild(cell);
            }
        }
    }

    // Pintar los bloques de clases seleccionados directamente en el grid del calendario
    function drawTimetableBlocks() {
        document.querySelectorAll('.timetable-block').forEach(block => block.remove());

        // Obtener un mapeo de curso -> índice único para alternar colores de forma estable
        const uniqueSelectedCourses = [...new Set(selectedSections.map(s => s.cursoId))];

        selectedSections.forEach(sec => {
            // Alternar los colores (Azul y Naranja UPAO) bloque por bloque para componentes de un mismo curso
            const courseSecs = selectedSections.filter(s => s.cursoId === sec.cursoId);
            const secIndex = courseSecs.findIndex(s => s.id === sec.id);
            const colorClass = (secIndex % 2 === 0) ? 'block-upao-blue' : 'block-upao-orange';

            sec.horarios.forEach(h => {
                const dayColumn = getDayColumnIndex(h.dia);
                if (dayColumn === -1) return;

                const startRow = timeToRowIndex(h.hora_ini, false);
                const endRow = timeToRowIndex(h.hora_fin, true);

                const block = document.createElement('div');
                block.className = `timetable-block ${colorClass}`;
                block.style.gridColumn = dayColumn.toString();
                block.style.gridRow = `${startRow} / ${endRow}`;

                block.innerHTML = `
                    <div class="timetable-block-title">${sec.cursoCodigo}</div>
                    <div class="timetable-block-meta">${sec.tipo === 'T' ? 'Teoría' : sec.tipo === 'P' ? 'Práctica' : 'Lab'} - Sec. ${sec.secc}</div>
                    <div class="timetable-block-meta-pill">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>
                        <span>${h.pabellon}-${h.aula || 'TBA'}</span>
                    </div>
                `;

                block.addEventListener('click', () => {
                    if (confirm(`¿Deseas quitar la sección del curso ${sec.cursoNombre}?`)) {
                        removeSection(sec.id);
                    }
                });

                timetableGrid.appendChild(block);
            });
        });
    }

    function getDayColumnIndex(diaStr) {
        const mapping = { 'LUN': 2, 'MAR': 3, 'MIE': 4, 'JUE': 5, 'VIE': 6, 'SAB': 7 };
        return mapping[diaStr.toUpperCase()] || -1;
    }

    function timeToRowIndex(timeStr, roundUp = false) {
        const [hourStr, minStr] = timeStr.split(':');
        let hour = parseInt(hourStr, 10);
        let min = parseInt(minStr, 10);

        if (roundUp) {
            if (min > 15) {
                hour += 1;
            }
        } else {
            if (min >= 30) {
                hour += 1;
            }
        }

        return (hour - 7) + 2;
    }

    // ══════════════════════════════════════════════
    // CONFIRMAR PROCESO DE MATRÍCULA
    // ══════════════════════════════════════════════
    btnConfirmEnroll.addEventListener('click', async () => {
        if (selectedSections.length === 0) return;

        conflictAlert.classList.add('hidden');

        // Validar si ha habido algún cambio con respecto a la matrícula cargada inicialmente
        const currentIds = selectedSections.map(s => s.id).sort();
        const initialIds = [...initialEnrolledSectionIds].sort();
        const noChanges = currentIds.length === initialIds.length && currentIds.every((id, idx) => id === initialIds[idx]);
        
        if (noChanges) {
            showConflictWarning('No has realizado ningún cambio en tu selección de horario actual para confirmar.');
            return;
        }

        // Validar que todos los cursos seleccionados tengan sus requerimientos completos (Teoría, Práctica y/o Lab)
        const uniqueSelectedCourses = [...new Set(selectedSections.map(s => s.cursoId))];
        for (const cursoId of uniqueSelectedCourses) {
            const curso = eligibleCourses.find(c => c.id === cursoId);
            if (curso) {
                const status = getCourseCompletionStatus(curso);
                if (status === 'incomplete') {
                    showConflictWarning(
                        `No se puede realizar la matrícula. Para el curso <strong>${curso.nombre}</strong> debes seleccionar todas sus componentes requeridas (Teoría, Práctica y/o Laboratorio) del mismo grupo.`
                    );
                    return;
                }
            }
        }

        btnConfirmEnroll.disabled = true;
        btnConfirmEnroll.textContent = 'Procesando...';

        try {
            const response = await fetch('/api/enroll', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    codigo: currentStudent.codigo,
                    seccion_ids: selectedSections.map(s => s.id)
                })
            });

            const data = await response.json();

            if (response.ok && data.success) {
                enrollSuccessModal.classList.remove('hidden');
            } else {
                alert(data.message || 'Ocurrió un error al procesar la matrícula.');
                btnConfirmEnroll.disabled = false;
                btnConfirmEnroll.textContent = 'Confirmar Matrícula';
            }
        } catch (err) {
            console.error('Error al realizar matrícula:', err);
            alert('Error de red. Por favor intente de nuevo.');
            btnConfirmEnroll.disabled = false;
            btnConfirmEnroll.textContent = 'Confirmar Matrícula';
        }
    });

    btnModalClose.addEventListener('click', () => {
        enrollSuccessModal.classList.add('hidden');
        loadDashboard(currentStudent.codigo);
    });

    // ==========================================
    // MANEJADORES DEL FORMULARIO Y RESULTADOS DEL PREDICTOR
    // ==========================================
    if (selectTrabaja) {
        selectTrabaja.addEventListener('change', () => {
            const trabaja = selectTrabaja.value === '1';
            inputHorasTrabajo.disabled = !trabaja;
            if (!trabaja) {
                inputHorasTrabajo.value = '0';
            }
        });
    }

    if (formPredictor) {
        formPredictor.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            if (!currentStudent) return;
            
            const btnRun = document.getElementById('btn-run-prediction');
            const originalText = btnRun.textContent;
            btnRun.textContent = 'Analizando...';
            btnRun.disabled = true;
            
            try {
                const seccionIds = selectedSections.map(s => s.id);
                const personalContext = {
                    trabaja: selectTrabaja.value,
                    horas_trabajo_semana: inputHorasTrabajo.value,
                    tiempo_traslado_diario: inputTraslado.value
                };
                
                const response = await fetch('/api/predict', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        codigo: currentStudent.codigo,
                        seccion_ids: seccionIds,
                        personal_context: personalContext
                    })
                });
                
                const resData = await response.json();
                
                if (response.ok && resData.success) {
                    const pred = resData.prediction;
                    
                    // Ocultar placeholder y mostrar contenido
                    predictPlaceholder.classList.add('hidden');
                    predictResultsContent.classList.remove('hidden');
                    
                    // Dibujar badge de clase
                    predictClassBadge.textContent = pred.predicted_class;
                    predictClassBadge.className = 'badge-result'; // reset
                    
                    const classLower = pred.predicted_class.toLowerCase();
                    if (classLower === 'excelente') predictClassBadge.classList.add('badge-excelente');
                    else if (classLower === 'bueno') predictClassBadge.classList.add('badge-bueno');
                    else if (classLower === 'regular') predictClassBadge.classList.add('badge-regular');
                    else if (classLower === 'deficiente') predictClassBadge.classList.add('badge-deficiente');
                    
                    // Dibujar barras de probabilidad
                    probBarsList.innerHTML = '';
                    const classesOrdered = ['Excelente', 'Bueno', 'Regular', 'Deficiente'];
                    classesOrdered.forEach(c => {
                        const pVal = pred.probabilities[c] || 0.0;
                        const pct = (pVal * 100).toFixed(1);
                        const fillClass = `fill-${c.toLowerCase()}`;
                        
                        const rowDiv = document.createElement('div');
                        rowDiv.className = 'prob-row';
                        rowDiv.innerHTML = `
                            <div class="prob-labels">
                                <span>${c}</span>
                                <span>${pct}%</span>
                            </div>
                            <div class="prob-track">
                                <div class="prob-fill ${fillClass}" style="width: ${pct}%"></div>
                            </div>
                        `;
                        probBarsList.appendChild(rowDiv);
                    });
                    
                    // Dibujar features calculados
                    featCreditos.textContent = pred.features.creditos_matriculados;
                    featDias.textContent = pred.features.dias_con_clases;
                    featMuertas.textContent = `${pred.features.horas_muertas_semana} hrs`;
                    featExigencia.textContent = pred.features.indice_exigencia_docentes.toFixed(2);
                    
                    // Dibujar recomendaciones
                    predictRecosList.innerHTML = '';
                    if (pred.recommendations && pred.recommendations.length > 0) {
                       pred.recommendations.forEach(r => {
                           const li = document.createElement('li');
                           li.textContent = r;
                           predictRecosList.appendChild(li);
                       });
                    } else {
                       const li = document.createElement('li');
                       li.textContent = 'No hay alertas ni recomendaciones críticas para este horario. ¡Excelente balance!';
                       predictRecosList.appendChild(li);
                    }
                    
                    // Dibujar métricas del modelo Naive Bayes
                    modelAccuracy.textContent = `${(pred.metrics.accuracy * 100).toFixed(1)}%`;
                    
                    let sumPrec = 0, sumF1 = 0, countClasses = 0;
                    for (const c in pred.metrics.classification_report) {
                        sumPrec += pred.metrics.classification_report[c].precision;
                        sumF1 += pred.metrics.classification_report[c].f1_score;
                        countClasses++;
                    }
                    const avgPrec = countClasses > 0 ? (sumPrec / countClasses) * 100 : 0;
                    const avgF1 = countClasses > 0 ? (sumF1 / countClasses) * 100 : 0;
                    
                    modelPrecision.textContent = `${avgPrec.toFixed(1)}%`;
                    modelF1.textContent = `${avgF1.toFixed(1)}%`;
                    
                    // Dibujar matriz de confusión
                    cmMatrixBody.innerHTML = '';
                    classesOrdered.forEach(r => {
                        const tr = document.createElement('tr');
                        tr.innerHTML = `<td style="font-weight: 700; text-align: left; background-color: #f8fafc;">${r}</td>`;
                        classesOrdered.forEach(p => {
                            const val = pred.metrics.confusion_matrix[r][p] || 0;
                            const isDiagonal = r === p;
                            const cellClass = isDiagonal ? 'cm-cell-diagonal' : (val > 0 ? 'cm-cell-error' : '');
                            tr.innerHTML += `<td class="${cellClass}">${val}</td>`;
                        });
                        cmMatrixBody.appendChild(tr);
                    });
                    
                    // Scroll suave
                    predictResultsContent.scrollIntoView({ behavior: 'smooth' });
                    
                } else {
                    alert(resData.message || 'Error al ejecutar la predicción.');
                }
            } catch (err) {
                console.error('Error ejecutando predictor:', err);
                alert('Ocurrió un error al contactar al servidor predictivo.');
            } finally {
                btnRun.textContent = originalText;
                btnRun.disabled = false;
            }
        });
    }

    // ══════════════════════════════════════════════
    // MODO OSCURO (DARK MODE)
    // ══════════════════════════════════════════════
    const btnThemeToggle = document.getElementById('btn-theme-toggle');
    if (btnThemeToggle) {
        const sunIcon = btnThemeToggle.querySelector('.sun-icon');
        const moonIcon = btnThemeToggle.querySelector('.moon-icon');
        
        // Cargar tema inicial
        if (localStorage.getItem('theme') === 'dark') {
            document.body.classList.add('dark-mode');
            if (sunIcon && moonIcon) {
                sunIcon.classList.remove('hidden');
                moonIcon.classList.add('hidden');
            }
        }
        
        btnThemeToggle.addEventListener('click', () => {
            const isDark = document.body.classList.toggle('dark-mode');
            if (isDark) {
                localStorage.setItem('theme', 'dark');
                if (sunIcon && moonIcon) {
                    sunIcon.classList.remove('hidden');
                    moonIcon.classList.add('hidden');
                }
            } else {
                localStorage.setItem('theme', 'light');
                if (sunIcon && moonIcon) {
                    sunIcon.classList.add('hidden');
                    moonIcon.classList.remove('hidden');
                }
            }
        });
    }
});
