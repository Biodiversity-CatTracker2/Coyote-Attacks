class Style:

	def __init__(self):
		pass

	@staticmethod
	def set_footer():
	    return """<style>
			footer {visibility: hidden;}
			footer::before {
				content:'© 2021 | NC State University & NC Museum of Natural Sciences | Developed and Maintained by Mohammad Alyetama'; 
				visibility: visible;
				position: fixed;
				left: 1;
				right: 1;
				bottom: 0;
				text-align: center;
				# color: green;
			}
		</style>"""

	@staticmethod
	def badge(name, image, link):
    	return f'<a href="{link}" target="_blank"><img alt="{name}" src="{image}"></a>'

    def get_badges(self):
	    streamlit_badge = self.badge(
	        'Streamlit',
	        'https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white',
	        'https://streamlit.io')
	    python_badge = self.badge(
	        'Python 3.10.0rc1',
	        'https://img.shields.io/badge/Python-FFD43B?style=for-the-badge&logo=python&logoColor=darkgreen',
	        'https://www.python.org/')
	    postgres_badge = self.badge(
	        'PostgreSQL',
	        'https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white',
	        'https://www.postgresql.org/')
	    docker_badge = self.badge(
	        'Docker',
	        'https://img.shields.io/badge/Docker-2CA5E0?style=for-the-badge&logo=docker&logoColor=white',
	        'https://www.docker.com/')
	    azure_badge = self.badge(
	        'Microsoft Azure',
	        'https://img.shields.io/badge/microsoft%20azure-0089D6?style=for-the-badge&logo=microsoft-azure&logoColor=white',
	        'https://azure.microsoft.com')
	    return f'###### Built with:<br>&nbsp;&nbsp;&nbsp;&nbsp;{streamlit_badge}&nbsp;&nbsp;{python_badge}&nbsp;&nbsp;{postgres_badge}&nbsp;&nbsp;{docker_badge}&nbsp;&nbsp;{azure_badge}'
