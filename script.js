const canvas = document.getElementById('bg-canvas');
const ctx = canvas.getContext('2d');

let particlesArray;
let mouse = {
    x: null,
    y: null,
    radius: 100
};

// Handle mouse move
window.addEventListener('mousemove', (event) => {
    mouse.x = event.x;
    mouse.y = event.y;
});

// Set canvas size
function setCanvasSize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
}

// Particle class
class Particle {
    constructor(x, y, vx, vy, size, color) {
        this.x = x;
        this.y = y;
        this.vx = vx;
        this.vy = vy;
        this.size = size;
        this.color = color;
        this.baseSize = size;
    }

    draw() {
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2, false);
        ctx.fillStyle = this.color;
        ctx.fill();
    }

    update() {
        // Bounce off walls
        if (this.x + this.size > canvas.width || this.x - this.size < 0) {
            this.vx = -this.vx;
        }
        if (this.y + this.size > canvas.height || this.y - this.size < 0) {
            this.vy = -this.vy;
        }

        this.x += this.vx;
        this.y += this.vy;

        // Mouse interaction
        let dx = mouse.x - this.x;
        let dy = mouse.y - this.y;
        let distance = Math.sqrt(dx * dx + dy * dy);

        if (distance < mouse.radius) {
            if (this.size < this.baseSize * 1.5) this.size += 0.2;
        } else if (this.size > this.baseSize) {
            this.size -= 0.1;
        }

        this.draw();
    }
}

// Create particle array
function init() {
    particlesArray = [];
    const isMobile = window.innerWidth < 768;
    const density = isMobile ? 15000 : 9000;
    let numberOfParticles = Math.min((canvas.height * canvas.width) / density, 150);

    for (let i = 0; i < numberOfParticles; i++) {
        let size = (Math.random() * 1.5) + 0.5;
        let x = Math.random() * (canvas.width - size * 2) + size;
        let y = Math.random() * (canvas.height - size * 2) + size;
        let vx = (Math.random() - 0.5) * (isMobile ? 0.3 : 0.5);
        let vy = (Math.random() - 0.5) * (isMobile ? 0.3 : 0.5);
        let color = 'rgba(0, 242, 254, 0.4)';
        particlesArray.push(new Particle(x, y, vx, vy, size, color));
    }
}

// Connect particles
function connect() {
    let opacityValue = 1;
    const maxLineDistance = window.innerWidth < 768 ? 80 : 120;

    for (let a = 0; a < particlesArray.length; a++) {
        for (let b = a + 1; b < particlesArray.length; b++) {
            let dx = particlesArray[a].x - particlesArray[b].x;
            let dy = particlesArray[a].y - particlesArray[b].y;
            let distance = Math.sqrt(dx * dx + dy * dy);

            if (distance < maxLineDistance) {
                opacityValue = 1 - (distance / maxLineDistance);
                ctx.strokeStyle = `rgba(0, 242, 254, ${opacityValue * 0.3})`;
                ctx.lineWidth = 0.5;
                ctx.beginPath();
                ctx.moveTo(particlesArray[a].x, particlesArray[a].y);
                ctx.lineTo(particlesArray[b].x, particlesArray[b].y);
                ctx.stroke();
            }
        }
    }
}

// Animation loop
function animate() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    for (let i = 0; i < particlesArray.length; i++) {
        particlesArray[i].update();
    }
    connect();
    requestAnimationFrame(animate);
}

// Throttled resize
let resizeTimeout;
window.addEventListener('resize', () => {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(() => {
        setCanvasSize();
        init();
    }, 200);
});

// Run
setCanvasSize();
init();
animate();
