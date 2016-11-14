============
Nittygriddy
============

Nitty griddy aims to make the deployment of analyses using the Aliroot/Aliphysics framework easy, transparent, and reproducible.
The primary goal is to completely eliminate the ungodly practice of copy-pasting together ``run.C`` files from all over the place.
A nittygriddy "project" requires the user to only provide the settings for the analysis itself - nothing else.
The way these settings are supplied is analogous to how one configures a wagon of a LEGO train.
The deployment in ``local`` (sequential), ``proof lite`` (local parallel) or ``grid`` is then completely transparent and does not require the editing of any files.
Nittygriddy also makes it easy to download parts of a desired dataset for local *offline* development - no need for running grid test mode.
On top of that, nittygriddy makes it easy to trigger the merging process once a grid analysis is finished.

And last but not least, nittygriddy does not do a "vendor lock-in": nittygriddy produces straight forward ``run.C`` files, stores them in a tidy folder structure and enables you to always rerun your analysis without nittygriddy in the future with a simple ``root run.C``.

.. image:: https://imgs.xkcd.com/comics/standards.png

Disclaimer
==========
I am using nittygriddy daily for quite a while now and find it to be extremely helpful. I think/hope that it could also be a great tool for others. However, you should not consider this project stable, ie I might change things that require adjustments on the users side. But as I said earlier, if that were to happen and you don't want to use nittygriddy anymore, you can always use the generated ``run.C`` files independently. If you have issues with nittygriddy, would love to see datasets added, or have any other comments and suggestions it is best to open an issue here on github or create a pull request straight away.


Installing nittygriddy
======================

In the future nittygriddy might be available on ``pypi``, but for the moment you have to do the following steps: ::

  $ git clone https://github.com/cbourjau/nittygriddy.git
  $ cd nittygriddy
  $ pip install -e .

This installs nittygriddy in ``editable`` mode, meaning that any changes to the files in the repository clone are immediately available to the command line tool without re-installation. This means that updates can be raked in with a simple ``git pull origin/master``.

Eitherway, the command ``nitty`` is now avialable on the command line, along with its hopefully helpful ``--help``.

Setting up a "project"
======================

What I call "a project" in the following is really nothing more than a folder where you store the settings for a specific analysis. Currently, all the settings are in one single file but more files might be added in the future. Also, note that in order to use nittygriddy **your task must be present in your local aliphysics installation** (which it really should anyways)!

configureWagon.C
----------------
The only ``.C`` file needed. It reflects setting up the options for your task analog to what is done in the lego trains. The shortest possible version, would look something like this: ::

  void configureWagon() {
    // Load you AddTask macro
    gROOT->LoadMacro("$ALICE_PHYSICS/PWGCF/Correlations/macros/c2/AddTaskC2.C");

    // Execute your AddTask macro. You can pass options in the function call if necessary
    AliAnalysisTaskC2* task =
      reinterpret_cast< AliAnalysisTaskC2* > (gROOT->ProcessLine("AddTaskC2()"));
    /*
      Set your options here, similar to what is done in the lego trains, eg:
      task->fSettings.fEtaAcceptanceLowEdge = -0.9;
    */
  }


..
   nittygriddy.json *(Not used, yet)*
   ----------------------------------
   This file contains some default options as well as depedencies which need to be loaded for execution. Again, this is analogus to the lego train interface. An example file might look like: ::

     [
       {
	   "Dependencies":"libOADB.so libSTEERBase.so libAOD.so libANALYSISalice.so libPWGCFCorrelationsC2.so"
       }
     ];


   datasets.json *(Not implemented, yet)*
   --------------------------------------
   This file contains information about custom datasets. If the standard ones are used this is not necessary.


Using Nittygriddy
=================

I'm lost::

  $ nitty --help
  
List all datasets::

  $ nitty datasets -l

Show details about a dataset::

  $ nitty datasets --show LHC10h_AOD160

Download 5GB of data from the given dataset for offline developing.
The files are saved in ``~/lhc_data/`` following the same folder structure as on the grid::

  $ nitty datasets --download LHC10h_AOD160 --volume=5

Run your analysis in proof lite locally::

  $ nitty run lite LHC10h_AOD160

Or submit it to the grid using a PARfile (see below)::
    
  $ nitty run grid LHC10h_AOD160 --par_files="PWGCFCorrelationsC2.par"

Once your analysis is finished on the grid, change to the output dir (``latest`` is a link pointing to the latest thing nittygriddy started) and trigger the merging::
    
  $ cd latest
  $ nitty merge online

Once all the final merging stages are reached, you can merge individual runs offline on your own computer::
    
  $ nitty merge offline

There are many more things you can do. Just check ``--help``.


Tips and Tricks
===============

PARfiles
--------
Par files can be used if you latest changes to your task are not yet in the latest aliphysics tag.
See Dario's `page <https://dberzano.github.io/2015/01/29/parfiles-reloaded>`_ for a bit more background. Long story short, if your task is properly set up in AliPhysics, you should be able to do::

  $ cd $ALICE_PHYSICS/../build
  $ make PWGCFCorrelationsC2.par # you can use TAB completion to find the right par file
  $ make -j$MJ install

This should create the .par file for your analysis in ``$ALICE_PHYSICS/PARfiles``. If you get an error instead, you might not have your analysis set up properly in cmake. Dario's post should have you covered.


My analysis crashes miserably when running in Proof lite
--------------------------------------------------------
Proof lite is quite picky about initializing your task's members in the constructors. This makes it a great test for running on the grid, but the error message is rather cryptic. Check if you initialized all your members in the constructor.

I get a crash if I do something grid related
--------------------------------------------
Do you have a valid alien-token? Its on the todo-list to ask for it more gracefully if its not present.


Migrate to LEGO trains
----------------------
Once your analysis works, you should be able to almost seamlessly use your configureWagon.C content in the LEGO wagon setup. Please use LEGO-trains whenever possible and reasonable to save resources!


Debug your code like a boss (with GDB)
--------------------------------------
There was a talk at one of the ALICE weeks about using GDB for debugging `(link) <https://indico.cern.ch/event/463952/>`_.
Unfortunately, the talk did not cover how to use GDB with your task in aliphysics.
Nittygriddy makes this quite easy now with the ``--wait_for_gdb`` option::

  $ nitty run local LHC10h_AOD160 --wait_for_gdb

The above sets up your analysis, prints out its process id (eg. 27575) and then waits for you to attach gdb. In principle it should be as easy as::

  $ gdb -p 27575

But there might be a few caveats. I wrote a small blog post about how to use gdb `here <http://cbourjau.github.io/alice/aliroot/aliphysics/2015/12/17/Debugging_aliphysics.html>`_.


What is happening behind the scene?
===================================

When running your analysis nitty griddy create a new folder in your project folder.
It then generates a ``run.C`` file from your options and copies it into that folder.
This ``run.C`` can be run on independently and should be easy to read.
This has the advantage that you can always just stop using ``nittygriddy`` and drop back to modifying the macros yourself - no vendor lockin!
However, if you would like to continue using ``nittygriddy``, you should not edit those macros directly since they might get overwritten and it defeats the purpose of this program in the first place.
