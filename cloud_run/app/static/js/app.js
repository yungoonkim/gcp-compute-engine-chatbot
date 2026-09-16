// Gemini Chatbot Frontend Application
document.addEventListener('DOMContentLoaded', () => {
  // DOM Elements
  const appLayout = document.getElementById('appLayout');
  const sidebar = document.getElementById('sidebar');
  const sidebarCollapseBtn = document.getElementById('sidebarCollapseBtn');
  const sidebarOpenBtn = document.getElementById('sidebarOpenBtn');
  const newChatBtn = document.getElementById('newChatBtn');
  const historyList = document.getElementById('historyList');
  const welcomeScreen = document.getElementById('welcomeScreen');
  const chatContainer = document.getElementById('chatContainer');
  const messagesWrapper = document.getElementById('messagesWrapper');
  const promptSection = document.getElementById('promptSection');
  const promptForm = document.getElementById('promptForm');
  const promptInput = document.getElementById('promptInput');
  const sendBtn = document.getElementById('sendBtn');
  const micBtn = document.getElementById('micBtn');
  const attachBtn = document.getElementById('attachBtn');
  const searchToggleBtn = document.getElementById('searchToggleBtn');
  const modelSelectTrigger = document.getElementById('modelSelectTrigger');
  const modelPillText = document.getElementById('modelPillText');
  const modelDropdownMenu = document.getElementById('modelDropdownMenu');
  const headerModelSelector = document.getElementById('headerModelSelector');
  const headerModelName = document.getElementById('headerModelName');
  const attachMenu = document.getElementById('attachMenu');
  const clearHistoryBtn = document.getElementById('clearHistoryBtn');
  const presetSummaryBtn = document.getElementById('presetSummaryBtn');
  const presetCodeBtn = document.getElementById('presetCodeBtn');
  const voiceToast = document.getElementById('voiceToast');
  const voiceStopBtn = document.getElementById('voiceStopBtn');
  const apiStatusDot = document.getElementById('apiStatusDot');
  const apiStatusText = document.getElementById('apiStatusText');
  const currentModelInfo = document.getElementById('currentModelInfo');

  // Application State
  let currentModel = localStorage.getItem('gemini_selected_model') || 'gemini-3.8-flash';
  let isSearchEnabled = localStorage.getItem('gemini_search_enabled') !== 'false';
  let conversations = JSON.parse(localStorage.getItem('gemini_chats') || '[]');
  let currentSessionId = null;
  let activeMessages = []; // [{role: 'user'|'assistant', content: '...', grounding?: ...}]
  let isGenerating = false;
  let recognition = null;

  // Initialize Marked.js renderer
  if (window.marked) {
    marked.setOptions({
      breaks: true,
      gfm: true,
      highlight: function (code, lang) {
        if (window.hljs && lang && hljs.getLanguage(lang)) {
          return hljs.highlight(code, { language: lang }).value;
        } else if (window.hljs) {
          return hljs.highlightAuto(code).value;
        }
        return code;
      }
    });
  }

  // --- Initial Setup & Health Check ---
  async function initApp() {
    // Check backend health & models
    try {
      const res = await fetch('/api/models');
      if (res.ok) {
        const data = await res.json();
        if (!data.api_key_configured) {
          apiStatusDot.classList.add('error');
          apiStatusText.textContent = 'API 키 누락';
        } else {
          apiStatusDot.classList.remove('error');
          apiStatusText.textContent = '정상 연결';
        }
      }
    } catch (e) {
      console.warn('API status check failed:', e);
      apiStatusDot.classList.add('error');
      apiStatusText.textContent = '서버 오프라인';
    }

    updateModelUI(currentModel);
    updateSearchToggleUI();
    renderHistoryList();
    resetToWelcomeScreen();
  }

  // --- Web Search Toggle ---
  function updateSearchToggleUI() {
    if (!searchToggleBtn) return;
    if (isSearchEnabled) {
      searchToggleBtn.classList.add('active');
      searchToggleBtn.title = '웹 실시간 검색 켜짐 (클릭 시 비활성화)';
    } else {
      searchToggleBtn.classList.remove('active');
      searchToggleBtn.title = '웹 실시간 검색 꺼짐 (클릭 시 활성화)';
    }
  }

  if (searchToggleBtn) {
    searchToggleBtn.addEventListener('click', () => {
      isSearchEnabled = !isSearchEnabled;
      localStorage.setItem('gemini_search_enabled', isSearchEnabled);
      updateSearchToggleUI();
    });
  }

  // --- UI State Transitions ---
  function resetToWelcomeScreen() {
    currentSessionId = 'chat_' + Date.now();
    activeMessages = [];
    messagesWrapper.innerHTML = '';
    welcomeScreen.classList.remove('hidden');
    chatContainer.classList.remove('active');
    promptSection.classList.add('initial-state');
    promptInput.value = '';
    updateSendBtnState();
    promptInput.focus();
  }

  function transitionToChatScreen() {
    if (welcomeScreen.classList.contains('hidden')) return;
    welcomeScreen.classList.add('hidden');
    promptSection.classList.remove('initial-state');
    chatContainer.classList.add('active');
  }

  // --- Model Selection ---
  function updateModelUI(modelId) {
    currentModel = modelId;
    localStorage.setItem('gemini_selected_model', modelId);

    const is38 = modelId.includes('3.8');
    const shortLabel = is38 ? 'Flash' : 'Flash 3.7';
    const fullLabel = is38 ? 'Gemini 3.8 Flash' : 'Gemini 3.7 Flash';

    modelPillText.textContent = shortLabel;
    headerModelName.textContent = is38 ? 'Flash 3.8' : 'Flash 3.7';

    if (currentModelInfo) {
      currentModelInfo.querySelector('.model-label-text').textContent = fullLabel;
    }

    // Update active highlight in dropdown
    document.querySelectorAll('.model-option').forEach(opt => {
      if (opt.dataset.model === modelId) {
        opt.classList.add('active');
      } else {
        opt.classList.remove('active');
      }
    });
  }

  function toggleModelMenu(e) {
    e.stopPropagation();
    attachMenu.classList.remove('show');
    modelDropdownMenu.classList.toggle('show');
  }

  modelSelectTrigger.addEventListener('click', toggleModelMenu);
  headerModelSelector.addEventListener('click', toggleModelMenu);

  document.querySelectorAll('.model-option').forEach(option => {
    option.addEventListener('click', () => {
      const selectedModel = option.dataset.model;
      updateModelUI(selectedModel);
      modelDropdownMenu.classList.remove('show');
    });
  });

  // Attach Menu Toggle
  attachBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    modelDropdownMenu.classList.remove('show');
    attachMenu.classList.toggle('show');
  });

  // Close popup menus on outside click
  document.addEventListener('click', () => {
    modelDropdownMenu.classList.remove('show');
    attachMenu.classList.remove('show');
  });

  clearHistoryBtn.addEventListener('click', () => {
    resetToWelcomeScreen();
  });

  presetSummaryBtn.addEventListener('click', () => {
    promptInput.value = '다음 내용을 핵심 위주로 3줄로 요약해줘:\n\n';
    promptInput.focus();
    updateSendBtnState();
    autoResizeTextarea();
  });

  presetCodeBtn.addEventListener('click', () => {
    promptInput.value = '다음 코드의 개선점 및 잠재적 버그를 분석해줘:\n\n```python\n\n```';
    promptInput.focus();
    updateSendBtnState();
    autoResizeTextarea();
  });

  // Sidebar controls
  sidebarCollapseBtn.addEventListener('click', () => {
    sidebar.classList.add('collapsed');
  });

  sidebarOpenBtn.addEventListener('click', () => {
    sidebar.classList.remove('collapsed');
  });

  newChatBtn.addEventListener('click', () => {
    resetToWelcomeScreen();
  });

  // --- Input & Send Logic ---
  function updateSendBtnState() {
    const hasText = promptInput.value.trim().length > 0;
    sendBtn.disabled = !hasText || isGenerating;
    if (hasText && !isGenerating) {
      sendBtn.classList.add('active');
    } else {
      sendBtn.classList.remove('active');
    }
  }

  function autoResizeTextarea() {
    promptInput.style.height = 'auto';
    const newHeight = Math.min(promptInput.scrollHeight, 180);
    promptInput.style.height = (newHeight > 24 ? newHeight : 24) + 'px';
  }

  promptInput.addEventListener('input', () => {
    updateSendBtnState();
    autoResizeTextarea();
  });

  promptInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!sendBtn.disabled) {
        handleSendMessage();
      }
    }
  });

  sendBtn.addEventListener('click', () => {
    if (!sendBtn.disabled) {
      handleSendMessage();
    }
  });

  // --- Messaging & Streaming Handling ---
  async function handleSendMessage() {
    const text = promptInput.value.trim();
    if (!text || isGenerating) return;

    transitionToChatScreen();

    // Reset Input
    promptInput.value = '';
    promptInput.style.height = 'auto';
    updateSendBtnState();

    // 1. Append User Message
    appendUserMessage(text);
    activeMessages.push({ role: 'user', content: text });

    // Save session title if first message
    updateSessionTitle(text);

    // 2. Prepare Assistant Message container
    const botMsgElements = createBotMessageElement(currentModel);
    messagesWrapper.appendChild(botMsgElements.container);
    scrollToBottom();

    isGenerating = true;
    updateSendBtnState();

    let fullBotReply = '';
    let currentGrounding = null;

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: activeMessages.map(m => ({ role: m.role, content: m.content })),
          model: currentModel,
          use_search: isSearchEnabled
        })
      });

      if (!response.ok) {
        throw new Error(`서버 응답 오류 (${response.status})`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop(); // keep unfinished line in buffer

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed.startsWith('data: ')) continue;

          const dataStr = trimmed.slice(6).trim();
          if (dataStr === '[DONE]') {
            break;
          }

          try {
            const dataObj = JSON.parse(dataStr);
            if (dataObj.error) {
              fullBotReply += `\n\n> ⚠️ **오류 발생**: ${dataObj.error}`;
            } else if (dataObj.text) {
              fullBotReply += dataObj.text;
            } else if (dataObj.grounding) {
              currentGrounding = dataObj.grounding;
              updateBotGroundingUI(botMsgElements, currentGrounding);
            }

            renderBotMarkdown(botMsgElements.body, fullBotReply, true);
            scrollToBottom();
          } catch (err) {
            console.error('SSE parse error:', err);
          }
        }
      }

    } catch (error) {
      fullBotReply += `\n\n> ⚠️ **통신 오류**: ${error.message}. 시스템 환경변수(GEMINI_API_KEY)와 네트워크 상태를 확인해주세요.`;
    } finally {
      // Finalize rendering without typing cursor
      renderBotMarkdown(botMsgElements.body, fullBotReply, false);
      addCodeCopyButtons(botMsgElements.body);
      if (currentGrounding) {
        updateBotGroundingUI(botMsgElements, currentGrounding);
      }
      activeMessages.push({
        role: 'assistant',
        content: fullBotReply,
        grounding: currentGrounding
      });
      saveCurrentConversation();
      isGenerating = false;
      updateSendBtnState();
      promptInput.focus();
    }
  }

  function appendUserMessage(text) {
    const msgDiv = document.createElement('div');
    msgDiv.className = 'chat-message user-message';
    msgDiv.innerHTML = `
      <div class="user-bubble">${escapeHtml(text)}</div>
    `;
    messagesWrapper.appendChild(msgDiv);
  }

  function createBotMessageElement(modelId) {
    const container = document.createElement('div');
    container.className = 'chat-message bot-message';

    const is38 = modelId.includes('3.8');
    const modelTag = is38 ? 'Gemini 3.8 Flash' : 'Gemini 3.7 Flash';

    container.innerHTML = `
      <div class="bot-avatar" title="${modelTag}">
        <img src="/static/gemini-icon.svg" alt="Gemini" class="bot-avatar-img">
      </div>
      <div class="bot-content-wrap">
        <div class="bot-header">
          <span class="bot-model-tag">${modelTag}</span>
        </div>
        <div class="bot-text-body">
          <span class="streaming-cursor"></span>
        </div>
        <div class="bot-grounding-area"></div>
        <div class="bot-actions">
          <button class="action-icon-btn copy-msg-btn" title="전체 답변 복사">
            <span class="material-symbols-rounded" style="font-size: 18px;">content_copy</span>
          </button>
        </div>
      </div>
    `;

    const header = container.querySelector('.bot-header');
    const body = container.querySelector('.bot-text-body');
    const groundingArea = container.querySelector('.bot-grounding-area');
    const copyBtn = container.querySelector('.copy-msg-btn');

    copyBtn.addEventListener('click', () => {
      const textToCopy = body.innerText || '';
      navigator.clipboard.writeText(textToCopy).then(() => {
        copyBtn.innerHTML = '<span class="material-symbols-rounded" style="font-size: 18px; color: #34a853;">check</span>';
        setTimeout(() => {
          copyBtn.innerHTML = '<span class="material-symbols-rounded" style="font-size: 18px;">content_copy</span>';
        }, 1500);
      });
    });

    return { container, header, body, groundingArea };
  }

  function updateBotGroundingUI(botMsgElements, grounding) {
    if (!grounding) return;
    const { header, groundingArea } = botMsgElements;

    // Add search badge to header if not already present
    if (header && !header.querySelector('.bot-search-tag')) {
      const searchTag = document.createElement('span');
      searchTag.className = 'bot-search-tag';
      searchTag.innerHTML = `
        <span class="material-symbols-rounded">travel_explore</span>
        <span>Google 실시간 검색됨</span>
      `;
      header.appendChild(searchTag);
    }

    if (!groundingArea) return;
    groundingArea.innerHTML = '';

    const wrap = document.createElement('div');
    wrap.className = 'grounding-sources-wrap';

    let html = '';

    // Search query chips
    if (grounding.queries && grounding.queries.length > 0) {
      html += `
        <div class="grounding-queries-list">
          ${grounding.queries.map(q => `
            <span class="grounding-query-chip" title="검색 쿼리">
              <span class="material-symbols-rounded">search</span>
              <span>${escapeHtml(q)}</span>
            </span>
          `).join('')}
        </div>
      `;
    }

    // Reference sources cards
    if (grounding.sources && grounding.sources.length > 0) {
      html += `
        <div class="grounding-sources-header">
          <span class="material-symbols-rounded">menu_book</span>
          <span>참고 출처 (${grounding.sources.length})</span>
        </div>
        <div class="grounding-sources-grid">
      `;

      grounding.sources.forEach(src => {
        let domain = '';
        try {
          if (src.title && !src.title.startsWith('http')) {
            domain = src.title;
          } else {
            const parsed = new URL(src.url);
            domain = parsed.hostname;
          }
        } catch (e) {
          domain = src.title || '웹 출처';
        }

        html += `
          <a href="${escapeHtml(src.url)}" target="_blank" rel="noopener noreferrer" class="grounding-source-card" title="${escapeHtml(src.title || src.url)}">
            <span class="material-symbols-rounded grounding-source-icon">public</span>
            <div class="grounding-source-details">
              <span class="grounding-source-title">${escapeHtml(src.title || domain)}</span>
              <span class="grounding-source-domain">${escapeHtml(domain)}</span>
            </div>
            <span class="material-symbols-rounded grounding-source-ext">open_in_new</span>
          </a>
        `;
      });

      html += `</div>`;
    }

    wrap.innerHTML = html;
    groundingArea.appendChild(wrap);
  }

  function renderBotMarkdown(element, rawText, isStreaming) {
    if (window.marked) {
      let parsed = marked.parse(rawText);
      if (isStreaming) {
        parsed += '<span class="streaming-cursor"></span>';
      }
      element.innerHTML = parsed;
    } else {
      element.textContent = rawText;
      if (isStreaming) {
        const cursor = document.createElement('span');
        cursor.className = 'streaming-cursor';
        element.appendChild(cursor);
      }
    }
  }

  function addCodeCopyButtons(container) {
    const preBlocks = container.querySelectorAll('pre');
    preBlocks.forEach((pre) => {
      if (pre.querySelector('.code-header-bar')) return;

      const codeElem = pre.querySelector('code');
      const langClass = codeElem ? Array.from(codeElem.classList).find(c => c.startsWith('language-')) : null;
      const lang = langClass ? langClass.replace('language-', '') : 'code';

      const headerBar = document.createElement('div');
      headerBar.className = 'code-header-bar';
      headerBar.innerHTML = `
        <span>${lang}</span>
        <button class="copy-code-btn">
          <span class="material-symbols-rounded" style="font-size: 16px;">content_copy</span>
          <span>코드 복사</span>
        </button>
      `;

      pre.insertBefore(headerBar, pre.firstChild);

      const copyBtn = headerBar.querySelector('.copy-code-btn');
      copyBtn.addEventListener('click', () => {
        const codeText = codeElem ? codeElem.innerText : pre.innerText;
        navigator.clipboard.writeText(codeText).then(() => {
          copyBtn.innerHTML = '<span class="material-symbols-rounded" style="font-size: 16px; color: #34a853;">check</span><span>복사됨!</span>';
          setTimeout(() => {
            copyBtn.innerHTML = '<span class="material-symbols-rounded" style="font-size: 16px;">content_copy</span><span>코드 복사</span>';
          }, 2000);
        });
      });
    });
  }

  function scrollToBottom() {
    chatContainer.scrollTop = chatContainer.scrollHeight;
  }

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  // --- Voice Input (Web Speech API) ---
  function setupSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      micBtn.title = '이 브라우저는 음성 입식을 지원하지 않습니다.';
      micBtn.style.opacity = '0.5';
      return;
    }

    recognition = new SpeechRecognition();
    recognition.lang = 'ko-KR';
    recognition.continuous = false;
    recognition.interimResults = true;

    recognition.onstart = () => {
      voiceToast.classList.add('listening');
    };

    recognition.onresult = (event) => {
      let transcript = '';
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        transcript += event.results[i][0].transcript;
      }
      promptInput.value = transcript;
      updateSendBtnState();
      autoResizeTextarea();
    };

    recognition.onerror = (event) => {
      console.warn('Speech recognition error:', event.error);
      voiceToast.classList.remove('listening');
    };

    recognition.onend = () => {
      voiceToast.classList.remove('listening');
      promptInput.focus();
    };

    micBtn.addEventListener('click', () => {
      try {
        recognition.start();
      } catch (err) {
        recognition.stop();
      }
    });

    voiceStopBtn.addEventListener('click', () => {
      if (recognition) recognition.stop();
    });
  }

  setupSpeechRecognition();

  // --- Chat History Storage ---
  function updateSessionTitle(firstPrompt) {
    let conv = conversations.find(c => c.id === currentSessionId);
    if (!conv) {
      conv = {
        id: currentSessionId,
        title: firstPrompt.length > 25 ? firstPrompt.substring(0, 25) + '...' : firstPrompt,
        timestamp: Date.now(),
        messages: []
      };
      conversations.unshift(conv);
    }
  }

  function saveCurrentConversation() {
    let conv = conversations.find(c => c.id === currentSessionId);
    if (conv) {
      conv.messages = activeMessages;
      conv.timestamp = Date.now();
      localStorage.setItem('gemini_chats', JSON.stringify(conversations));
      renderHistoryList();
    }
  }

  function renderHistoryList() {
    historyList.innerHTML = '';
    if (conversations.length === 0) {
      historyList.innerHTML = '<div style="font-size: 0.85rem; color: var(--text-muted); padding: 8px 12px;">대화 기록이 없습니다.</div>';
      return;
    }

    conversations.forEach(conv => {
      const item = document.createElement('div');
      item.className = 'history-item' + (conv.id === currentSessionId ? ' active' : '');
      item.innerHTML = `
        <span class="history-item-text" title="${escapeHtml(conv.title)}">${escapeHtml(conv.title)}</span>
        <button class="history-item-delete" title="삭제">
          <span class="material-symbols-rounded" style="font-size: 16px;">delete</span>
        </button>
      `;

      item.querySelector('.history-item-text').addEventListener('click', () => {
        loadConversation(conv.id);
      });

      item.querySelector('.history-item-delete').addEventListener('click', (e) => {
        e.stopPropagation();
        deleteConversation(conv.id);
      });

      historyList.appendChild(item);
    });
  }

  function loadConversation(id) {
    const conv = conversations.find(c => c.id === id);
    if (!conv) return;

    currentSessionId = conv.id;
    activeMessages = conv.messages || [];

    welcomeScreen.classList.add('hidden');
    promptSection.classList.remove('initial-state');
    chatContainer.classList.add('active');
    messagesWrapper.innerHTML = '';

    activeMessages.forEach(msg => {
      if (msg.role === 'user') {
        appendUserMessage(msg.content);
      } else {
        const botEl = createBotMessageElement(currentModel);
        renderBotMarkdown(botEl.body, msg.content, false);
        addCodeCopyButtons(botEl.body);
        if (msg.grounding) {
          updateBotGroundingUI(botEl, msg.grounding);
        }
        messagesWrapper.appendChild(botEl.container);
      }
    });

    renderHistoryList();
    scrollToBottom();
  }

  function deleteConversation(id) {
    conversations = conversations.filter(c => c.id !== id);
    localStorage.setItem('gemini_chats', JSON.stringify(conversations));
    if (currentSessionId === id) {
      resetToWelcomeScreen();
    }
    renderHistoryList();
  }

  // App boot
  initApp();
});
