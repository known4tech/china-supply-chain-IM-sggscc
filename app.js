// Application Data
const appData = {
    china_gdp_data: {
        "Year": [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025],
        "GDP_Growth_Rate": [6.75, 6.0, 2.24, 8.45, 2.95, 5.25, 5.0, 5.2],
        "GDP_Trillion_USD": [13.9, 14.3, 14.7, 17.8, 17.9, 17.8, 18.2, 18.5],
        "Manufacturing_PMI": [50.8, 50.2, 51.9, 50.9, 50.1, 49.7, 49.5, 49.4]
    },
    china_fdi_data: {
        "Year": [2019, 2020, 2021, 2022, 2023, 2024],
        "FDI_Billion_USD": [140, 163, 344, 190, 163, 116],
        "BOP_FDI_Billion_USD": [78, 149, 344, 180, 51.3, 18.6],
        "Manufacturing_FDI_Share": [25, 27, 30, 28, 25, 27]
    },
    us_imports_data: {
        "Country": ["China", "Mexico", "Vietnam", "India", "ASEAN", "Germany", "Canada"],
        "Share_2018": [21.2, 13.6, 2.4, 2.3, 6.8, 4.8, 10.5],
        "Share_2023": [13.9, 15.4, 4.1, 3.2, 9.2, 4.5, 13.7],
        "Growth_2018_2022": [-10, 18, 65, 44, 65, -5, 12]
    },
    trade_war_data: {
        "Year": [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025],
        "US_Tariff_Rate_China": [7.4, 19.3, 19.3, 19.3, 19.3, 25, 35, 51.1],
        "China_Tariff_Rate_US": [8.0, 20.7, 20.7, 20.7, 20.7, 22, 28, 32.6],
        "US_China_Trade_Billion": [659, 559, 559, 657, 690, 664, 575, 520]
    },
    company_cases: {
        "Company": ["Apple", "Nike", "Tesla", "Samsung"],
        "China_Production_Share_2018": [70, 45, 100, 35],
        "China_Production_Share_2024": [50, 30, 60, 25],
        "Alternative_Countries": ["India,Vietnam", "Vietnam,Indonesia", "Germany,Mexico", "Vietnam,India"],
        "Diversification_Investment_Billion": [22, 5.2, 15, 8.5]
    },
    alt_countries_data: {
        "Country": ["Vietnam", "India", "Mexico"],
        "FDI_Manufacturing_2023_USD_Billion": [12.1, 8.5, 35.2],
        "Manufacturing_Growth_2019_2023": [27, 35, 22],
        "GDP_Per_Capita_2024": [4081, 2088, 12500],
        "Labor_Cost_Index": [35, 28, 55]
    }
};

// Global presentation controller variable
let presentationController = null;

// Fullscreen functionality with better error handling
function toggleFullscreen() {
    console.log('Toggle fullscreen called');
    try {
        if (!document.fullscreenElement && 
            !document.webkitFullscreenElement && 
            !document.mozFullScreenElement && 
            !document.msFullscreenElement) {
            
            console.log('Entering fullscreen');
            // Enter fullscreen
            const element = document.documentElement;
            const fullscreenPromise = element.requestFullscreen ? element.requestFullscreen() :
                                    element.webkitRequestFullscreen ? element.webkitRequestFullscreen() :
                                    element.mozRequestFullScreen ? element.mozRequestFullScreen() :
                                    element.msRequestFullscreen ? element.msRequestFullscreen() :
                                    null;
            
            if (fullscreenPromise) {
                fullscreenPromise.catch(err => {
                    console.error('Error entering fullscreen:', err);
                    alert('Fullscreen mode not supported or blocked by browser');
                });
            } else if (element.webkitRequestFullscreen) {
                element.webkitRequestFullscreen();
            } else if (element.mozRequestFullScreen) {
                element.mozRequestFullScreen();
            } else if (element.msRequestFullscreen) {
                element.msRequestFullscreen();
            } else {
                alert('Fullscreen is not supported by this browser');
            }
        } else {
            console.log('Exiting fullscreen');
            // Exit fullscreen
            if (document.exitFullscreen) {
                document.exitFullscreen();
            } else if (document.webkitExitFullscreen) {
                document.webkitExitFullscreen();
            } else if (document.mozCancelFullScreen) {
                document.mozCancelFullScreen();
            } else if (document.msExitFullscreen) {
                document.msExitFullscreen();
            }
        }
    } catch (error) {
        console.error('Fullscreen toggle error:', error);
        alert('Error toggling fullscreen mode');
    }
}

function updateFullscreenButton() {
    console.log('Updating fullscreen button');
    const fullscreenBtn = document.getElementById('fullscreenBtn');
    if (fullscreenBtn) {
        if (document.fullscreenElement || 
            document.webkitFullscreenElement || 
            document.mozFullScreenElement || 
            document.msFullscreenElement) {
            fullscreenBtn.textContent = '⛶ Exit Fullscreen';
            console.log('Fullscreen button updated to Exit');
        } else {
            fullscreenBtn.textContent = '⛶ Fullscreen';
            console.log('Fullscreen button updated to Enter');
        }
    } else {
        console.error('Fullscreen button not found!');
    }
}

// Presentation Logic
class PresentationController {
    constructor() {
        this.currentSlide = 1;
        this.totalSlides = 16;
        this.charts = {};
        console.log('Presentation Controller initialized');
        this.init();
    }

    init() {
        console.log('Initializing presentation...');
        this.setupEventListeners();
        this.updateSlideCounter();
        this.updateNavigationButtons();
        // Delay chart initialization to ensure DOM is ready
        setTimeout(() => this.initializeCharts(), 500);
    }

    setupEventListeners() {
        console.log('Setting up event listeners...');
        
        // Navigation buttons
        const prevBtn = document.getElementById('prevBtn');
        const nextBtn = document.getElementById('nextBtn');
        const fullscreenBtn = document.getElementById('fullscreenBtn');

        if (prevBtn) {
            console.log('Previous button found, adding listener');
            prevBtn.addEventListener('click', (e) => {
                console.log('Previous button clicked');
                e.preventDefault();
                e.stopPropagation();
                this.previousSlide();
            });
        } else {
            console.error('Previous button not found!');
        }

        if (nextBtn) {
            console.log('Next button found, adding listener');
            nextBtn.addEventListener('click', (e) => {
                console.log('Next button clicked');
                e.preventDefault();
                e.stopPropagation();
                this.nextSlide();
            });
        } else {
            console.error('Next button not found!');
        }

        if (fullscreenBtn) {
            console.log('Fullscreen button found, adding listener');
            fullscreenBtn.addEventListener('click', (e) => {
                console.log('Fullscreen button clicked');
                e.preventDefault();
                e.stopPropagation();
                toggleFullscreen();
            });
        } else {
            console.error('Fullscreen button not found!');
        }

        // Fullscreen change event listeners with better browser support
        const fullscreenEvents = [
            'fullscreenchange', 
            'webkitfullscreenchange', 
            'mozfullscreenchange', 
            'MSFullscreenChange'
        ];
        
        fullscreenEvents.forEach(event => {
            document.addEventListener(event, () => {
                console.log('Fullscreen change event:', event);
                updateFullscreenButton();
            });
        });

        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            console.log('Key pressed:', e.key);
            
            if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
                e.preventDefault();
                this.previousSlide();
            }
            if (e.key === 'ArrowRight' || e.key === 'ArrowDown' || e.key === ' ') {
                e.preventDefault();
                this.nextSlide();
            }
            if (e.key === 'Home') {
                e.preventDefault();
                this.goToSlide(1);
            }
            if (e.key === 'End') {
                e.preventDefault();
                this.goToSlide(this.totalSlides);
            }
            if (e.key === 'F11' || (e.key === 'f' && e.ctrlKey)) {
                e.preventDefault();
                toggleFullscreen();
            }
            if (e.key === 'p' && e.ctrlKey) {
                e.preventDefault();
                window.print();
            }
        });

        // Click navigation on slides (but not on nav controls)
        document.addEventListener('click', (e) => {
            // Skip if clicking on navigation controls, buttons, or other interactive elements
            if (e.target.closest('.nav-controls') || 
                e.target.closest('button') || 
                e.target.closest('.presenter-field') ||
                e.target.tagName === 'INPUT' ||
                e.target.tagName === 'BUTTON') {
                return;
            }
            
            if (e.target.closest('.slide')) {
                if (e.clientX > window.innerWidth / 2) {
                    this.nextSlide();
                } else {
                    this.previousSlide();
                }
            }
        });

        console.log('Event listeners setup complete');
    }

    nextSlide() {
        console.log('Next slide called, current:', this.currentSlide, 'total:', this.totalSlides);
        if (this.currentSlide < this.totalSlides) {
            this.goToSlide(this.currentSlide + 1);
        } else {
            console.log('Already at last slide');
        }
    }

    previousSlide() {
        console.log('Previous slide called, current:', this.currentSlide);
        if (this.currentSlide > 1) {
            this.goToSlide(this.currentSlide - 1);
        } else {
            console.log('Already at first slide');
        }
    }

    goToSlide(slideNumber) {
        console.log('Going to slide:', slideNumber, 'from current:', this.currentSlide);
        
        // Validate slide number
        if (slideNumber < 1 || slideNumber > this.totalSlides) {
            console.log('Invalid slide number:', slideNumber);
            return;
        }

        // Hide current slide
        const currentSlideEl = document.querySelector(`[data-slide="${this.currentSlide}"]`);
        if (currentSlideEl) {
            currentSlideEl.classList.remove('active');
            console.log('Removed active class from slide', this.currentSlide);
        } else {
            console.error('Current slide element not found:', this.currentSlide);
        }

        // Show target slide
        const targetSlideEl = document.querySelector(`[data-slide="${slideNumber}"]`);
        if (targetSlideEl) {
            targetSlideEl.classList.add('active');
            this.currentSlide = slideNumber;
            this.updateSlideCounter();
            this.updateNavigationButtons();
            console.log('Successfully navigated to slide', slideNumber);
        } else {
            console.error('Target slide element not found:', slideNumber);
        }
    }

    updateSlideCounter() {
        const counter = document.getElementById('slideCounter');
        if (counter) {
            counter.textContent = `${this.currentSlide} / ${this.totalSlides}`;
            console.log('Slide counter updated:', counter.textContent);
        } else {
            console.error('Slide counter element not found!');
        }
    }

    updateNavigationButtons() {
        const prevBtn = document.getElementById('prevBtn');
        const nextBtn = document.getElementById('nextBtn');

        if (prevBtn) {
            const isFirstSlide = this.currentSlide === 1;
            prevBtn.disabled = isFirstSlide;
            prevBtn.style.opacity = isFirstSlide ? '0.5' : '1';
            prevBtn.style.cursor = isFirstSlide ? 'not-allowed' : 'pointer';
        }

        if (nextBtn) {
            const isLastSlide = this.currentSlide === this.totalSlides;
            nextBtn.disabled = isLastSlide;
            nextBtn.style.opacity = isLastSlide ? '0.5' : '1';
            nextBtn.style.cursor = isLastSlide ? 'not-allowed' : 'pointer';
        }

        console.log('Navigation buttons updated for slide', this.currentSlide);
    }

    initializeCharts() {
        console.log('Initializing charts...');
        try {
            this.createGDPChart();
            this.createFDIChart();
            this.createTradeWarChart();
            this.createImportChart();
            this.createCorporateChart();
            console.log('Charts initialized successfully');
        } catch (error) {
            console.error('Error initializing charts:', error);
        }
    }

    createGDPChart() {
        const ctx = document.getElementById('gdpChart');
        if (!ctx) {
            console.log('GDP chart canvas not found');
            return;
        }

        this.charts.gdp = new Chart(ctx, {
            type: 'line',
            data: {
                labels: appData.china_gdp_data.Year,
                datasets: [
                    {
                        label: 'GDP Growth Rate (%)',
                        data: appData.china_gdp_data.GDP_Growth_Rate,
                        borderColor: '#1FB8CD',
                        backgroundColor: 'rgba(31, 184, 205, 0.1)',
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4
                    },
                    {
                        label: 'Manufacturing PMI',
                        data: appData.china_gdp_data.Manufacturing_PMI,
                        borderColor: '#FFC185',
                        backgroundColor: 'rgba(255, 193, 133, 0.1)',
                        borderWidth: 2,
                        fill: false,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'China GDP Growth Rate & Manufacturing PMI Trends',
                        font: { size: 16, weight: 'bold' }
                    },
                    legend: {
                        display: true,
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'GDP Growth Rate (%)'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Manufacturing PMI'
                        },
                        grid: {
                            drawOnChartArea: false,
                        },
                    }
                }
            }
        });
        console.log('GDP chart created');
    }

    createFDIChart() {
        const ctx = document.getElementById('fdiChart');
        if (!ctx) {
            console.log('FDI chart canvas not found');
            return;
        }

        this.charts.fdi = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: appData.china_fdi_data.Year,
                datasets: [
                    {
                        label: 'Total FDI (Billion USD)',
                        data: appData.china_fdi_data.FDI_Billion_USD,
                        backgroundColor: '#1FB8CD',
                        borderColor: '#1FB8CD',
                        borderWidth: 1
                    },
                    {
                        label: 'BOP FDI (Billion USD)',
                        data: appData.china_fdi_data.BOP_FDI_Billion_USD,
                        backgroundColor: '#B4413C',
                        borderColor: '#B4413C',
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'China Foreign Direct Investment Collapse',
                        font: { size: 16, weight: 'bold' }
                    },
                    legend: {
                        display: true,
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Investment (Billion USD)'
                        }
                    }
                }
            }
        });
        console.log('FDI chart created');
    }

    createTradeWarChart() {
        const ctx = document.getElementById('tradeWarChart');
        if (!ctx) {
            console.log('Trade war chart canvas not found');
            return;
        }

        this.charts.tradeWar = new Chart(ctx, {
            type: 'line',
            data: {
                labels: appData.trade_war_data.Year,
                datasets: [
                    {
                        label: 'US Tariffs on China (%)',
                        data: appData.trade_war_data.US_Tariff_Rate_China,
                        borderColor: '#DB4545',
                        backgroundColor: 'rgba(219, 69, 69, 0.1)',
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4
                    },
                    {
                        label: 'China Tariffs on US (%)',
                        data: appData.trade_war_data.China_Tariff_Rate_US,
                        borderColor: '#D2BA4C',
                        backgroundColor: 'rgba(210, 186, 76, 0.1)',
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Trade War: Escalating Tariff Rates',
                        font: { size: 16, weight: 'bold' }
                    },
                    legend: {
                        display: true,
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Tariff Rate (%)'
                        }
                    }
                }
            }
        });
        console.log('Trade war chart created');
    }

    createImportChart() {
        const ctx = document.getElementById('importChart');
        if (!ctx) {
            console.log('Import chart canvas not found');
            return;
        }

        this.charts.import = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: appData.us_imports_data.Country,
                datasets: [
                    {
                        label: '2018 Import Share (%)',
                        data: appData.us_imports_data.Share_2018,
                        backgroundColor: '#FFC185',
                        borderColor: '#FFC185',
                        borderWidth: 1
                    },
                    {
                        label: '2023 Import Share (%)',
                        data: appData.us_imports_data.Share_2023,
                        backgroundColor: '#1FB8CD',
                        borderColor: '#1FB8CD',
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'US Import Diversification: Country Share Changes',
                        font: { size: 16, weight: 'bold' }
                    },
                    legend: {
                        display: true,
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Import Share (%)'
                        }
                    }
                }
            }
        });
        console.log('Import chart created');
    }

    createCorporateChart() {
        const ctx = document.getElementById('corporateChart');
        if (!ctx) {
            console.log('Corporate chart canvas not found');
            return;
        }

        this.charts.corporate = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: appData.company_cases.Company,
                datasets: [
                    {
                        label: '2018 China Production Share (%)',
                        data: appData.company_cases.China_Production_Share_2018,
                        backgroundColor: '#B4413C',
                        borderColor: '#B4413C',
                        borderWidth: 1
                    },
                    {
                        label: '2024 China Production Share (%)',
                        data: appData.company_cases.China_Production_Share_2024,
                        backgroundColor: '#1FB8CD',
                        borderColor: '#1FB8CD',
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Corporate Supply Chain Diversification',
                        font: { size: 16, weight: 'bold' }
                    },
                    legend: {
                        display: true,
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        title: {
                            display: true,
                            text: 'China Production Share (%)'
                        }
                    }
                }
            }
        });
        console.log('Corporate chart created');
    }
}

// Initialize everything when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing presentation...');
    
    // Initialize presentation controller
    presentationController = new PresentationController();
    
    // Initialize fullscreen button state
    setTimeout(() => {
        updateFullscreenButton();
    }, 100);
    
    console.log('Presentation initialized successfully');
    
    // Debug: List all buttons found
    const buttons = document.querySelectorAll('button');
    console.log('Found buttons:', buttons.length);
    buttons.forEach((btn, index) => {
        console.log(`Button ${index}:`, btn.id, btn.textContent, btn.className);
    });
});