// Normaliseert Notion-rijen (GO 4IT-Studio Prospects) en versleutelt met AES-256-GCM (PBKDF2-SHA256, 310000 iteraties).
// Logo's en screenshots zitten ALLEEN in de versleutelde payload.
const fs=require('fs'),crypto=require('crypto');
const [,,inF,outF,pwF]=process.argv;
const pw=fs.readFileSync(pwF,'utf8').trim();
const raw=JSON.parse(fs.readFileSync(inF,'utf8'));
const rd=f=>fs.existsSync(f)?JSON.parse(fs.readFileSync(f,'utf8')):{};
const logos=rd('private/logos.json'),shots=rd('private/shots.json');
const dom=w=>{try{return new URL(/:\/\//.test(w)?w:'https://'+w).hostname.toLowerCase().replace(/^www\./,'')}catch(e){return null}};
const rows=(Array.isArray(raw)?raw:raw.results||[]).map(r=>{const o={};for(const[k,v]of Object.entries(r)){let key=k,val=v;
 if(k.startsWith('date:')){if(!k.endsWith(':start'))continue;key=k.split(':')[1];}
 if(val==='__YES__')val=true;if(val==='__NO__')val=false;
 if(typeof val==='string'&&val.startsWith('[')){try{val=JSON.parse(val)}catch(e){}}
 if(val!==null&&val!==''&&val!==false)o[key]=val;}
 const d=dom(o.Website||'');if(d){o._domain=d;if(logos[d])o._logo=logos[d];const s=shots[d];if(s&&s.img){o._shot=s.img;o._shotDate=new Date(s.t*1000).toISOString().slice(0,10);o._https=s.https}}
 return o;});
const docs={werkwijze:fs.existsSync('WERKWIJZE.md')?fs.readFileSync('WERKWIJZE.md','utf8'):'',hoe:fs.existsSync('HOE-HET-WERKT.md')?fs.readFileSync('HOE-HET-WERKT.md','utf8'):''};
const payload=Buffer.from(JSON.stringify({updated:new Date().toISOString(),rows,docs}));
const salt=crypto.randomBytes(16),iv=crypto.randomBytes(12),iter=310000;
const key=crypto.pbkdf2Sync(pw,salt,iter,32,'sha256');
const c=crypto.createCipheriv('aes-256-gcm',key,iv);
const ct=Buffer.concat([c.update(payload),c.final(),c.getAuthTag()]);
fs.writeFileSync(outF,JSON.stringify({v:1,kdf:'PBKDF2-SHA256',iter,salt:salt.toString('base64'),iv:iv.toString('base64'),ct:ct.toString('base64')}));
console.log(`Versleuteld: ${rows.length} rijen, ${rows.filter(r=>r._shot).length} screenshots, ${rows.filter(r=>r._logo).length} logo's -> ${outF} (${(fs.statSync(outF).size/1024|0)} KB)`);
