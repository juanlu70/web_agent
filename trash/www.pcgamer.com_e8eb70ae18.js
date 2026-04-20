const o=()=>{const o=window.location.host.split(".");return"local"===o[0]&&o.shift(),"www"!==o[0]&&"global"!==o[0]||o.shift(),o.join(".")};export{o as g};
