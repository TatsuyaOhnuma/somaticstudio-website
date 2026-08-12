/** @type {import('tailwindcss').Config} */
module.exports = {
  // public配下のHTMLを走査して、実際に使われているクラスだけをCSSに出力する。
  // index.html内のJavaScript（テンプレートリテラル）に書かれたクラスも対象になる。
  content: ['./public/**/*.html'],
  theme: {
    extend: {
      colors: {
        brand: '#5a6e5a',
        canvas: '#f9f9f7'
      }
    }
  },
  plugins: []
};
