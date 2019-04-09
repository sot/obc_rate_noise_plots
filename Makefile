# Set the task name
TASK = obc_rate_noise_plots

# Uncomment the correct choice indicating either SKA or TST flight environment
FLIGHT_ENV = SKA

# Set the names of all files that get installed
SHARE = plot_recent_rates.py task_schedule.cfg
WWW = index.html

include /proj/sot/ska/include/Makefile.FLIGHT

install:
#  Uncomment the lines which apply for this task
	mkdir -p $(INSTALL_SHARE)
	rsync --times --cvs-exclude $(SHARE) $(INSTALL_SHARE)/
	mkdir -p $(INSTALL_DATA)
	mkdir -p $(SKA)/www/ASPECT/obc_rate_noise/trending
	rsync --times --cvs-exclude $(WWW) $(SKA)/www/ASPECT/obc_rate_noise/trending
