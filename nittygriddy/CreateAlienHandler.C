#include "TString.h"
#include "AliAnalysisAlien.h"
#include "GetSetting.C"

enum {kGRID_FULL, kGRID_OFFLINE, kGRID_TEST, kGRID_MERGE_ONLINE, kGRID_MERGE_OFFLINE};
TString kALICE_PHYSICS = "vAN-20160405-1";

AliAnalysisGrid* CreateAlienHandler(Int_t gridMode, Bool_t isMC) {
  // Create a generic alien grid handler. Ie, one still needs to add the analysis files to the plugin
  AliAnalysisAlien *plugin = new AliAnalysisAlien();

  plugin->AddIncludePath("-I. -I$ROOTSYS/include -I$ALICE_ROOT/include -I$ALICE_PHYSICS/include");
  plugin->SetAdditionalLibs("libOADB.so libSTEERBase.so");
  plugin->SetOverwriteMode();
  plugin->SetExecutableCommand("aliroot -q -b");
  // Can be "full", "test", "offline", "submit" or "merge"
  // merging only works in "full" mode?!
  if (kGRID_OFFLINE == gridMode){
    plugin->SetRunMode("offline");
    // The following option is necessary to write the merge jdl's
    plugin->SetMergeViaJDL(true);
  }
  else if (kGRID_TEST == gridMode)
    plugin->SetRunMode("test");
  else if (kGRID_FULL == gridMode) {
    plugin->SetRunMode("full");
    plugin->SetMergeViaJDL(true);
  }
  else if (kGRID_MERGE_ONLINE == gridMode){
    plugin->SetRunMode("terminate");
    plugin->SetMergeViaJDL(true);
  }
  else if (kGRID_MERGE_OFFLINE == gridMode){
    plugin->SetRunMode("terminate");
    plugin->SetMergeViaJDL(false);  // turn this to false after the final merging to merge runs
  }

  plugin->SetNtestFiles(1);
  //Set versions of used packages
  plugin->SetAliPhysicsVersion(kALICE_PHYSICS);

  // Declare input data to be processed
  plugin->SetGridDataDir(GetSetting("datadir"));
  plugin->SetDataPattern(GetSetting("datadir_pattern"));
  plugin->SetGridWorkingDir(GetSetting("workdir"));
  plugin->SetAnalysisMacro("myAnalysisMacro.C");
  plugin->SetExecutable("myAnalysisExec.sh");
  plugin->SetJDLName("myTask.jdl");
  plugin->SetDropToShell(false);  // do not open a shell
  plugin->SetRunPrefix(GetSetting("run_number_prefix")); 
  plugin->AddRunList(getSetting("run_list"));
  plugin->SetGridOutputDir("output");
  plugin->SetMaxMergeFiles(25);
  plugin->SetMergeExcludes("EventStat_temp.root"
			   "event_stat.root");
  // Use run number as output folder names
  plugin->SetOutputToRunNo();
  plugin->SetTTL(15*3600);
  // Optionally set input format (default xml-single)
  plugin->SetInputFormat("xml-single");
  // Optionally modify job price (default 1)
  plugin->SetPrice(1);      
  // Optionally modify split mode (default 'se')    
  //plugin->SetSplitMaxInputFileNumber();
  plugin->SetSplitMode("se");
  return plugin;
};
