/* 
 * This is an automatically generated file. Do yourself a favour and
 * do __not__ edit it by hand. It will be overwritten eventually and
 * you will be sad. Instead file an issue over at the nittygriddy
 * gitlab page, please.
 */

#ifndef __CINT__
#include <assert.h>
#include <fstream>
#include <iostream>
#include <vector>

#include "TROOT.h"
#include "TProof.h"
#include "TChain.h"
#include "TObject.h"
#include "TList.h"
#include "TString.h"

#include "AliAnalysisManager.h"
#include "AliMCEventHandler.h"
#include "AliESDInputHandler.h"
#include "AliAODInputHandler.h"
#include "AliAnalysisGrid.h"
#include "AliAnalysisAlien.h"
#include "AliMultSelectionTask.h"
#include "AddTaskC2.C"

#include "GetSetting.C"

#endif
#include <stdlib.h>     /* atoi */

enum {kLOCAL, kLITE, kPOD, kGRID};
enum {kGRID_FULL, kGRID_OFFLINE, kGRID_TEST, kGRID_MERGE_ONLINE, kGRID_MERGE_OFFLINE};

void loadLibs(const TString extralibs, const Int_t runmode){
  if (runmode == kLOCAL || runmode == kGRID){
    // for running with root only
    gSystem->Load("libTree.so");
    gSystem->Load("libGeom.so");
    gSystem->Load("libVMC.so");
    gSystem->Load("libSTEERBase.so");
    gSystem->Load("libESD.so");
    gSystem->Load("libAOD.so"); 

    // load extra analysis libs
    TIter it(extralibs.Tokenize(" "));
    TObjString *lib = 0;
    while ((lib = dynamic_cast<TObjString *>(it()))){
      if (gSystem->Load(lib->String()) < 0) {
	std::cout << "Error loading " << lib->String() << std::endl;
      }
    }
  }
  else{
    TList *list = new TList();
    list->Add(new TNamed("ALIROOT_EXTRA_LIBS", extralibs.ReplaceAll(" ", ":").Data()));
    TString alicePar;
    
    if ((runmode == kLITE)){
      alicePar  = "$ALICE_ROOT/ANALYSIS/macros/AliRootProofLite.par";
    }
    
    if (runmode == kPOD){
      // A single AliRoot package for *all* AliRoot versions: new on VAF
      alicePar = "/afs/cern.ch/alice/offline/vaf/AliceVaf.par";
      list->Add(new TNamed("ALIROOT_ENABLE_ALIEN", "1"));  // important: creates token on every PROOF worker
    }
    gProof->UploadPackage(alicePar.Data());
    gProof->EnablePackage(alicePar.Data(), list);  // this "list" is the same as always
    std::cout << "enabled packages: " << std::endl;
    gProof->ShowEnabledPackages();
  }
}

TChain* makeChain() {
  TChain * chain = new TChain ("aodTree");
  TString incollection = "./input_files.dat";
  ifstream file_collect(incollection.Data());
  TString line;
  while (line.ReadLine(file_collect) ) {
    chain->Add(line.Data());
  }
  return chain;
}


void setUpIncludes(Int_t runmode) {
  // Set the include directories
  // gProof is without -I :P and gSystem has to be set for all runmodes
  gSystem->AddIncludePath("-I$ALICE_ROOT/include");
  if (runmode == kLITE){
    gProof->AddIncludePath("$ALICE_ROOT/include", kTRUE);
  }
}

AliAnalysisGrid* CreateAlienHandler(const std::string gridMode) {
  // Create a generic alien grid handler.
  AliAnalysisAlien *plugin = new AliAnalysisAlien();

  plugin->AddIncludePath("-I. -I$ROOTSYS/include -I$ALICE_ROOT/include -I$ALICE_PHYSICS/include");
  plugin->SetAdditionalLibs(("libOADB.so libSTEERBase.so " + GetSetting("par_files")).c_str());
  // if (GetSetting("par_files")  != "") {
  //   plugin->SetupPar(GetSetting("par_files").c_str());
  //   }
  plugin->SetOverwriteMode();
  plugin->SetExecutableCommand("aliroot -q -b");
  // The following option is necessary to write the merge jdl's
  plugin->SetMergeViaJDL(true);

  // Can be "full", "test", "offline", "submit" or "merge"
  // merging only works in "full" mode?!
  if (gridMode == "offline"){
    plugin->SetRunMode(gridMode.c_str());
  }
  else if (gridMode == "test"){
    plugin->SetRunMode(gridMode.c_str());
  }
  else if (gridMode == "full"){
    plugin->SetRunMode(gridMode.c_str());
  }
  else if (gridMode == "merge_online"){
    plugin->SetRunMode("terminate");
  }
  else if (gridMode == "merge_offline"){
    plugin->SetRunMode("terminate");
    plugin->SetMergeViaJDL(false);
  }
  else {
    std::cout << "Invalid gridMode!" << std::endl;
    assert(0);
  }
  plugin->SetNtestFiles(1);
  //Set versions of used packages
  plugin->SetAliPhysicsVersion(GetSetting("aliphysics_version").c_str());

  // Declare input data to be processed
  plugin->SetGridDataDir(GetSetting("datadir").c_str());
  plugin->SetDataPattern(GetSetting("data_pattern").c_str());
  plugin->SetGridWorkingDir(GetSetting("workdir").c_str());
  plugin->SetAnalysisMacro(TString::Format("Macro_%s.C", GetSetting("workdir").c_str()));
  plugin->SetExecutable(TString::Format("Exec_%s.sh", GetSetting("workdir").c_str()));
  plugin->SetJDLName(TString::Format("Task_%s.jdl", GetSetting("workdir").c_str()));
  plugin->SetDropToShell(false);  // do not open a shell
  plugin->SetRunPrefix(GetSetting("run_number_prefix").c_str());
  plugin->AddRunList(GetSetting("run_list").c_str());
  plugin->SetGridOutputDir("output");
  plugin->SetMaxMergeFiles(25);
  plugin->SetMergeExcludes("EventStat_temp.root"
			   "event_stat.root");
  // Use run number as output folder names
  plugin->SetOutputToRunNo();
  plugin->SetTTL(atoi(GetSetting("ttl").c_str()));
  // Optionally set input format (default xml-single)
  plugin->SetInputFormat("xml-single");
  // Optionally modify job price (default 1)
  plugin->SetPrice(1);      
  // Optionally modify split mode (default 'se')    
  //plugin->SetSplitMaxInputFileNumber();
  plugin->SetSplitMode("se");
  return plugin;
};


void run(const std::string gridMode="")
{
  // load GetSetting.C macro to allow access to settings for this particular dataset
  gROOT->LoadMacro("./GetSetting.C");
  Int_t max_events = -1;
  Int_t runmode = -1;
  if (GetSetting("wait_for_gdb") == "true"){
    cout << "Execution is paused so that you cann attach gdb to the running process:" << endl;
    cout << "gdb -p " << gSystem->GetPid() << endl;
    cout << "Press any key to continue" << endl;
    std::cin.ignore();
  }
  if (GetSetting("runmode") == "local")
    runmode = kLOCAL;
  else if (GetSetting("runmode") == "lite")
    runmode = kLITE;
  else if (GetSetting("runmode") == "grid")
    runmode = kGRID;
  else {
    std::cout << "Invalid analysis mode: " << GetSetting("runmode") << "! I have no idea whats going on..." << std::endl;
    assert(0);
  }
  // start proof if necessary
  TString proofUrl = "";
  if (runmode == kLITE) {
    proofUrl += "lite://";
    if (GetSetting("nworkers") != "-1"){
      proofUrl += "?workers=";
      proofUrl += GetSetting("nworkers");
    }
  } else if (runmode == kPOD) {
    proofUrl += "pod://";
  }
  if (proofUrl.Length()) {
    TProof::Open(proofUrl);
  }

  setUpIncludes(runmode);

  // Create  and setup the analysis manager
  AliAnalysisManager *mgr = new AliAnalysisManager();

  TString analysisName("AnalysisResults");
  mgr->SetCommonFileName(analysisName + TString(".root"));

  // Set Handlers TODO: depends on dataset type
  AliVEventHandler* aodH = new AliAODInputHandler;
  mgr->SetInputEventHandler(aodH);
  //AliMCEventHandler* handler = new AliMCEventHandler;
  //handler->SetReadTR(kTRUE);
  //mgr->SetMCtruthEventHandler(handler);

  if (runmode == kGRID) {
    gROOT->LoadMacro("./CreateAlienHandler.C");
    AliAnalysisGrid *alienHandler = CreateAlienHandler(gridMode);
    if (!alienHandler) return;
    mgr->SetGridHandler(alienHandler);
  }

  // Add tasks
  gROOT->LoadMacro("$ALICE_PHYSICS/OADB/COMMON/MULTIPLICITY/macros/AddTaskMultSelection.C");
  AliMultSelectionTask * task = AddTaskMultSelection(kFALSE);
  // I think SetAlternateOADBforEstimators is depreciated (comment in .h file)
  if (GetSetting("overwrite_oadb_period") != ""){
    task->SetAlternateOADBforEstimators(GetSetting("overwrite_oadb_period").c_str());
  }

  gROOT->LoadMacro("./ConfigureWagon.C");
  ConfigureWagon();

  if (!mgr->InitAnalysis()) return;
  mgr->PrintStatus();

  if (runmode == kGRID) {
    std::cout << "Starting grid analysis" << std::endl;
    mgr->StartAnalysis("grid");
  }
  else if ((runmode == kLOCAL) || (runmode == kLITE)) {
      // Process with chain
    TChain *chain = makeChain();
      if (!chain) {
	std::cout << "Dataset is empty!" << std::endl;
	return;
      }
      if (runmode == kLITE)
	mgr->StartAnalysis("proof", chain, max_events);

      else if (runmode == kLOCAL) {
	// in order to be inconvinient, aliroot does interprete max_events differently for proof and local :P
	if (max_events == -1) mgr->StartAnalysis("local", chain);
	else mgr->StartAnalysis("local", chain, max_events);
      }
    }
}
