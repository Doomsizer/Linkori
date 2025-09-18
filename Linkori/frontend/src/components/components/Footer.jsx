import React from "react";
import "../../styles/Footer.css"
import githubLogo from "../../media/github.svg"
import tgLogo from "../../media/telegram.svg"
import discordLogo from "../../media/discord.svg"
import osuLogo from "../../media/osu.svg"

const Footer = () => {
    return (
        <footer>
            <div className="footer-contact">
                <a href="https://github.com/Doomsizer/Linkori/"><img className="footer-github" src={githubLogo} alt="github repo of the site"/></a>
                <a href="https://t.me/D0omik/"><img className="footer-telegram" src={tgLogo} alt="telegram contact of the creator"/></a>
                <a href="https://discord.com/users/1134761492328226847"><img className="footer-discord" src={discordLogo} alt="discord contact of the creator"/></a>
                <a href="https://osu.ppy.sh/users/24625610"><img className="footer-osu" src={osuLogo} alt="osu profile of the creator"/></a>
            </div>
            <span className="footer-copyright">&copy;Linkori 2025</span>
        </footer>
    );
};

export default Footer;