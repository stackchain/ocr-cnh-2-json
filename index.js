const e = require('express')
const m = require('multer')
const s = require('child_process').spawn;

const a = e()
const p = 8080
const upload = m({ 
  dest : '/tmp/',
})

a.use(e.static('public'))

const runPy = file => new Promise(function(resolve, reject) {
  const p = s('python', ['-W', 'ignore', 'main.py', '--image', `${file}`]);
  p.stdout.on('data', function(data) {
      resolve(data);
  });
  p.stderr.on('data', (data) => {
      reject(data);
  });
});

a.post('/cnh.json', upload.single('file'), (r, a, e) => {
  if (!r.file) return a.status(400).json({ Error: 'Something went wrong'})
  let file = r.file.path
  runPy(file)
  .then(d => a.json(`${d}`))
  .catch(d => a.status(400).json({ Error: `Something went wrong - ${d}`}))
})
a.listen(p, _ => console.log(`Running on ${p}`))