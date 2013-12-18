The Everything is Connected Engine (EiCE)
==================================
This repository contains the code to the Everything is Connected Engine, the server behind the http://everythingisconnected.be application. EIC is a Linked Data application for automatically generating a story between two concepts in the Web of Data, based on formally described links. A path between two concepts is obtained by browsing linked open datasets; the path is then enriched with multimedia presentation material for each node in order to obtain a full multimedia presentation of the found path. An efficient technique combining pre-processing and indexing of RDF datasets is used, which is able to find paths in a couple of seconds.

## License

Copyright 2012, Multimedia Lab - Ghent University - iMinds

Licensed under AGPL Version 3 license <http://www.gnu.org/licenses/agpl-3.0.html> .

## Client

The Everything Is Connected client was released under the same license and can be found here: https://github.com/mmlab/eic-gui

## Additional documentation and publications

* [Discovering Meaningful Connections between Resources in the Web of Data](http://ceur-ws.org/Vol-996/papers/ldow2013-paper-04.pdf)
L. De Vocht et al., <i>Proceedings of the 6th Workshop on Linked Data on the Web</i>
* [Everything is Connected: Using Linked Data for Multimedia Narration of Connections between Concepts](http://iswc2012.semanticweb.org/sites/default/files/paper_10.pdf)
M. Vander Sande et al. <i>Best Demo award ISWC2012 </i>
* Presentation at [USC-ISI](http://www.isi.edu): 
	[Slides](http://www.slideshare.net/MielSande/presentation-isi2-26181326)
	[Webcast](http://webcasterms1.isi.edu/mediasite/SilverlightPlayer/Default.aspx?peid=45b27e6ddec34405a638789183ac85421d)

#  Install guide

This document will guide you through all the necessary steps to install the Everything is Connected Engine 1.0. 
All sources for Section 1 of this document are Open Source and can be found on the Web. The sources for Section 2,3,4, except for some, are copyrighted by iMinds - Multimedia Lab and are available under AGPLv3 license. 

Pathfinding: git@github.com:mmlab/eice.git

## 1.	Install SIREn

The engine uses the indexer SIREn, an extension of SOLR for RDF, originally made for the Semantic Web index Sindice. 

### 1.0 Preparation 

Install Ubuntu 12.10 or higher. If you need to do an upgrade of an existing version, run the following command.

	sudo do-release-upgrade -d

Fix efi with the boot-repair tool for ubuntu if you cannot boot.

Get the sources at

	git clone git@github.com:rdelbru/SIREn.git

Install Maven

	sudo apt-get install maven2

Install Tomcat 6 (or 7)

	sudo apt-get install tomcat6

Export the catalina folder, this is default

	export CATALINA_BASE=/var/lib/tomcat6


### 1.1	Stop Tomcat

Stop your tomcat instance before performing the following steps. 

	/etc/init.d/tomcat6 stop

### 1.2	Clean Previously Installed Siren

In order to avoid unexpected conflict with previously deployed Solr webapp,  
remove siren webapp directory

	rm -rf $CATALINA_BASE/webapps/siren

### 1.3	Copying Context File
Create the folder ``$CATALINA_BASE/conf/Catalina/localhost/``

	sudo mkdir -p $CATALINA_BASE/conf/Catalina/localhost

Copy siren.xml to:

	cp siren-solr/example/siren.xml $CATALINA_BASE/conf/Catalina/localhost/siren.xml

### 1.4	Configure Solr/SIREn Webapp

Set an environment variable ``SOLR_HOME`` pointing to the folder ``/your/local/path/siren-solr/example/solr``

	export SOLR_HOME=/your/local/path/siren-solr/example/solr


Edit siren.xml to both set the path of the war file and ``SOLR_HOME`` correctly

	<Context docBase="/your/local/path/siren-solr/example/apache-solr-3.5.0.war" debug="0" crossContext="true" >
		<Environment name="solr/home" type="java.lang.String" value="/your/local/path/siren-solr/example/solr" override="true" />
	</Context>

### 1.5	Copying SIREn libs

You can build SIREn using Maven in the main folder. First, make sure the ``JAVA_HOME`` is set correctly to the right JDK.

Next, the "caliper" dependency is no longer available. Change the pom.xml to the prior 0.5-rc1 version:

    <dependency>
      <groupId>com.google.caliper</groupId>
      <artifactId>caliper</artifactId>
      <version>0.5-rc1</version>
      <scope>test</scope>
    </dependency>

Then you can build using the command

	mvn package

Copy ``siren-core-0.2.3-SNAPSHOT.jar``, 
``siren-qparser-0.2.3-SNAPSHOT.jar`` and ``siren-solr-0.2.3-SNAPSHOT.jar`` in 
``SOLR_HOME/lib``.

	sudo cp siren-core/target/siren-core-0.2.3-SNAPSHOT.jar $SOLR_HOME/lib
	sudo cp siren-qparser/target/siren-qparser-0.2.3-SNAPSHOT.jar $SOLR_HOME/lib
	sudo cp siren-solr/target/siren-solr-0.2.3-SNAPSHOT.jar $SOLR_HOME/lib


### 1.6	Change File Permissions

Ensure that tomcat has full file permissions on ``SOLR_HOME``:

	chown -R tomcat6:tomcat6 $SOLR_HOME chown -R tomcat6:tomcat6 $SOLR_HOME

### 1.7	Start Tomcat

Start tomcat

	/etc/init.d/tomcat6 start

You should be able to access the Solr admin page at 
  [http://localhost:8080/siren/]()
  
If problems would occur, see ``$CATALINA_BASE/logs/catalina.out``

## 2	Configuring the indexing

Unpack ``indexer.tar``, supplied in the home directory of these sources.

	tar xvzf indexer.tar

In the folder "indexer", make sure you will find, amongst others, the following files:

	required_siren_schema_with_lookup.xml
	required_siren_schema.xml

These are possible index configurations for SIREn. They need to be modified if specific search functionality is required.

Replace the schema.xml in ``$SOLR_HOME/conf/`` with the configuration file of your choosing.

	cp required_siren_schema.xml $SOLR_HOME/conf/schema.xml
	
Restart tomcat after this.

	/etc/init.d/tomcat6 start	

## 3 Ingesting RDF

To run the ingesting scripts, NodeJS 8.25 is required on your system. If this is not yet case, go ahead and install it.

	wget http://nodejs.org/dist/v0.8.25/node-v0.8.25-linux-x64.tar.gz
	tar zxf node-v0.8.25-linux-x64.tar.gz
	export PATH=$PATH:<location_of_node_dir>/node-v0.8.25-linux-x64/bin
	
For the next steps, you'll needs several scripts from the "indexer" folder:

	nquads-to-sirendoc
	nquads_or_triples-to-sirendoc
	indexer.py
	dataset_preparation.py
	loader.py
	
It is very important to keep your files organized throughout the process, so make sure you have a good strategy. 

### 3.1 Convert Quads or Triples to SIREn docs

To index triples or quads, we need to convert them to SIREn docs first. This can be done with the nodejs scripts ``nquads-to-sirendoc``or ``nquads_or_triples-to-sirendoc``.

You can run the script as follows, with ``<nquad_source>`` as the triple file that needs to be ingested and ``<siren_docs_folder>`` as the folder where the files need to be stored. Make sure you use full paths!!

	./nquads-to-sirendoc <nquad source> <siren_docs_folder>
	
This will create an archive in the destination folder. 
	
	DE-XXXXX.tar.gz

#### Sidenote

The script ``dataset_preparation.py``has the same functionality as mentioned above. However, it is capable to handle multiple folders and files, and convert RDF/XML automatically. Also, it merges triples with the same subjects across different files, which improves efficiency when sorting and avoids indexing doubles.

### 3.2 Load the SIREn docs

When the docs are created, they need to be loaded into SIREn. This is done by running the python script ``loader.py``.

	python loader.py <siren_docs_folder>

Make sure the jar-file ``siren-eostool-0.2.2-SNAPSHOT-assembly.jar`` is present in the same folder as the script. 

In case the above jar is incompatible with the system it's running on, a custom build might be required. This application is a customized version of the SIREn Entity Tool. The source code is made available on github: 

	git clone git@github.com:mielvds/eic-entity-tool.git
	

## 4. Running the pathfinding service

### 4.1 Install python 3 and the required dependencies

Install python 3 and the necessary libraries.

	sudo apt-get install python3 python3-tornado python3-numpy python3-scipy python3-setuptools python3-mako python3-dev python3-lxml
	
Build and install ujson from source.
	
	git clone git@github.com:esnme/ultrajson.git
	cd ultrajson
	sudo python3 setup.py install

Build and install cython from source.
	
	sudo apt-get install cython
	git cone git@github.com:fantix/gevent.git
	cd gevent
	sudo python3 setup.py install
	
Build and install requests from source.
	
	git clone git://github.com/kennethreitz/requests.git
	cd requests
	sudo python3 setup.py install
	
Build and install SPARQLWrapper from source, install Subversion first to get it.
	
	sudo apt-get install subversion
	svn checkout svn://svn.code.sf.net/p/sparql-wrapper/code/trunk sparql-wrapper-code
	cd sparql-wrapper-code/src
	sudo python3 setup.py install
	
Build and install networkx from source.
	
	git clone git@github.com:networkx/networkx.git
	cd networkx
	sudo python3 setup.py install
	
Build and install matplotlib and some of its dependencies from source.

	sudo apt-get install libfreetype6-dev libpng12-dev
	
	wget http://labix.org/download/python-dateutil/python-dateutil-2.0.tar.gz
	tar xzvf python-dateutil-2.0.tar.gz
	cd python-dateutil-2.0
	sudo python3 setup.py install
	
	git clone git@github.com:matplotlib/matplotlib.git
	cd matplotlib
	sudo python3 setup.py install
	
Build and install graphtool. You'll need to install some extra repositories in your system with the following commands.
	
	deb http://downloads.skewed.de/apt/DISTRIBUTION DISTRIBUTION universe
	deb-src http://downloads.skewed.de/apt/DISTRIBUTION DISTRIBUTION universe

where DISTRIBUTION can be raring, quantal, or precise
	
Next, add a public key to prevent the authentication error message to pop up everytime you use ``apt-get``. Finally, install the package.
	
	gpg --keyserver pgp.skewed.de --recv-key 0x04DC461EF36FE35D && gpg --export --armor 0x04DC461EF36FE35D | sudo apt-key add -
	sudo apt-get update
	sudo apt-get install python3-graph-tool

### 4.2	Running the pathfinding server

Make a copy of ``EiCGraphAlgo/core/config.ini`` and call it config_local.ini . Set the different parameters accordingly.

	cp config.ini config_local.ini
	

Run the ``server.py``script. Your server should be available under [http://localhost:8888/]()

	python3 server.py
	
The search algorithm uses a blacklist and a list of valid domains. The blacklist contains all predicates that need to be ignored while looking for a path. The list of valid domains contains all the 'namespaces' to search in. This can be useful, for example, to avoid dead ends caused by unindexed resources.

You can configure the black list and valid domains in ``config_search.py``.

	
	



