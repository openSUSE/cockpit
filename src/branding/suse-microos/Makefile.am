susemicroosbrandingdir = $(datadir)/cockpit/branding/suse-microos

dist_susemicroosbranding_DATA = \
	src/branding/suse-microos/branding.css \
	$(NULL)

install-data-hook::
	$(LN_S) -f /usr/share/wallpapers/SLEdefault/contents/images/1920x1200.png $(DESTDIR)$(susemicroosbrandingdir)/default-1920x1200.png
	$(LN_S) -f /usr/share/pixmaps/distribution-logos/square-hicolor.svg $(DESTDIR)$(susemicroosbrandingdir)/square-hicolor.svg
	$(LN_S) -f /usr/share/pixmaps/distribution-logos/favicon.ico $(DESTDIR)$(susemicroosbrandingdir)/favicon.ico
	$(LN_S) -f /usr/share/pixmaps/distribution-logos/apple-touch-icon.png $(DESTDIR)$(susemicroosbrandingdir)/apple-touch-icon.png
