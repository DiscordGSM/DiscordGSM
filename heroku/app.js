const debugPort = 7999
const heroku = process.env.PORT != null
const express = require('express')
const https = require('https')
const path = require('path')
const fs = require('fs')
const version = new RegExp("VERSION.{0,}=.{0,}'(.*)'").exec(fs.readFileSync(path.join(__dirname, '/../bot.py')))[1] // Get DiscordGSM verison from bot.py
const serversJson = heroku ? process.env.SERVERS_JSON : fs.readFileSync(path.join(__dirname, '/../servers.json')) // Get servers.json data
const inviteLink = require('child_process').execSync(`${(heroku ? 'python3 ' : '')}getbotinvitelink.py`, { encoding : 'utf-8' }) // Get bot invite link by getbotinvitelink.py

const app = express()
app.set('view engine', 'ejs')
app.use(express.json())
app.use(express.static(path.join(__dirname, '/public')))
app.use('/', (_, res) => {
    // Check servers.json valid
    try {
        var JsonValid = JSON.parse(serversJson) | true
    } catch {
        var JsonValid = false
    }

    // Render in ejs
    res.render(path.join(__dirname, '/public/index.ejs'), { 
        version: version,
        inviteLink: inviteLink,
        SERVERS_JSON: JsonValid ? '✔️' : '❌',
        DGSM_TOKEN: inviteLink.includes('https://discord.com/api/oauth2/authorize?client_id=') ? '✔️' : '❌',
    })
})
app.listen(heroku ? process.env.PORT : debugPort)

if (process.env.HEROKU_APP_NAME != null) {
    setInterval(() => https.get(`https://${process.env.HEROKU_APP_NAME}.herokuapp.com?t=${+new Date()}`), 5 * 60 * 1000)
} else {
    console.log('ERROR: HEROKU_APP_NAME Config Var not found')
}

console.log('DiscordGSM - Heroku Version started successfully.' + (heroku ? '': ` Local: http://localhost:${debugPort}`))
