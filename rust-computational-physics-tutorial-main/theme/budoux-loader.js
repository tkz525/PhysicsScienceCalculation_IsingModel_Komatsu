/**
 * BudouX Web Components を使った日本語分節改行
 *
 * このスクリプトは、ページ内の日本語テキストを自動的に
 * 文節単位で改行できるように <wbr> タグを挿入します。
 */

(function () {
  'use strict';

  // BudouX Web Components の CDN URL
  const BUDOUX_CDN = 'https://unpkg.com/budoux/bundle/budoux-ja.min.js';

  /**
   * BudouX スクリプトを動的に読み込む
   */
  function loadBudouX() {
    return new Promise((resolve, reject) => {
      // すでに読み込まれている場合はスキップ
      if (customElements.get('budoux-ja')) {
        resolve();
        return;
      }

      const script = document.createElement('script');
      script.src = BUDOUX_CDN;
      script.async = true;
      script.onload = () => resolve();
      script.onerror = () => reject(new Error('Failed to load BudouX'));
      document.head.appendChild(script);
    });
  }

  /**
   * 指定された要素内のテキストノードを <budoux-ja> でラップする
   * @param {Element} element - 処理対象の要素
   */
  function wrapTextWithBudouX(element) {
    // 処理対象外の要素
    const excludeTags = new Set([
      'SCRIPT', 'STYLE', 'CODE', 'PRE', 'KBD', 'SAMP', 'VAR',
      'BUDOUX-JA', 'TEXTAREA', 'INPUT', 'SVG', 'MATH', 'NOSCRIPT'
    ]);

    // 日本語を含むかチェックする正規表現
    const japaneseRegex = /[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]/;

    /**
     * 再帰的にテキストノードを処理
     * @param {Node} node - 処理対象のノード
     */
    function processNode(node) {
      // 除外タグの場合はスキップ
      if (node.nodeType === Node.ELEMENT_NODE && excludeTags.has(node.tagName)) {
        return;
      }

      // テキストノードの場合
      if (node.nodeType === Node.TEXT_NODE) {
        const text = node.textContent;

        // 日本語を含み、空白のみでない場合のみ処理
        if (japaneseRegex.test(text) && text.trim().length > 0) {
          const budouxElement = document.createElement('budoux-ja');
          budouxElement.textContent = text;
          node.parentNode.replaceChild(budouxElement, node);
        }
        return;
      }

      // 子ノードを処理（ライブコレクションの変更を避けるため配列にコピー）
      const children = Array.from(node.childNodes);
      children.forEach(processNode);
    }

    processNode(element);
  }

  /**
   * メインコンテンツを処理
   */
  async function processContent() {
    try {
      await loadBudouX();

      // メインコンテンツ領域を取得
      const main = document.querySelector('main');
      if (!main) {
        console.warn('BudouX: main element not found');
        return;
      }

      // 処理対象の要素
      const selectors = [
        'p',
        'li',
        'td',
        'th',
        'dd',
        'dt',
        'blockquote',
        'h1',
        'h2',
        'h3',
        'h4',
        'h5',
        'h6',
        'figcaption',
        'caption',
        'summary'
      ];

      // 各要素を処理
      selectors.forEach(selector => {
        main.querySelectorAll(selector).forEach(wrapTextWithBudouX);
      });

    } catch (error) {
      console.error('BudouX loading failed:', error);
      // BudouX の読み込みに失敗しても、CSS の word-break: auto-phrase で
      // フォールバックされるため、致命的ではない
    }
  }

  // DOM の準備ができたら実行
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', processContent);
  } else {
    processContent();
  }
})();
