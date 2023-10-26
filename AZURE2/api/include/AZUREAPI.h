#ifndef AZUREAPI_H
#define AZUREAPI_H

#include "AZUREMain.h"

#include "Constants.h"
#include <vector>

class Config;
class EData;
class CNuc;

///A function class to perform the calculation of the chi-squared value

/*!
 * The AZUREAPI function class calculates the cross section based on a 
 * parameter set for all available data, and returns a chi-squared value.
 * This function class is what Minuit calls repeatedly during the fitting
 * process to perform the minimization.
 */

class AZUREAPI {
 public:
  /*!
   * The AZUREAPI object is created with reference to an EData and CNuc object.
   *. The runtime configurations are also passed through a Config structure.
   */
  AZUREAPI(Config& configure) : configure_(configure) { };
  
  ~AZUREAPI() {};

  bool Initialize( );

  // Update data objects, returns number of segments
  int UpdateData( );
  // Update segments values
  int UpdateSegments(vector_r& p);
  // Calculate the external capture for data
  bool CalculateExternalCapture( );
  // Reads the parameters values
  bool UpdateParameters( );
  // Reads the norms values
  void UpdateNorms( );
  // Set AZURE2 to calculate data points
  void SetData( );
  // Set AZURE2 to calculate extrapolations
  void SetExtrap( );
  // Set radius to a fixed value
  void SetRadius( int idx, double r );
  
  /*!
   * Returns a reference to the Config structure.
   */
  Config &configure() const {return configure_;};
  /*!
   * Returns a pointer to the EData object.
   */
  EData *data() const {return data_;};
  /*!
   * Returns a pointer to the CNuc object.
   */
  CNuc *compound() const {return compound_;};
  /*!
   * Returns a pointer to the parameter values object.
   */
  vector_r params_values() const {return transform_;};
  /*!
   * Returns a pointer to the parameter names object.
   */
  std::string params_names(int i) const {return names_[i];};
  /*!
   * Returns a pointer to the parameter names object.
   */
  std::vector<bool> params_fixed() const {return fixed_;};
  /*!
   * Returns a pointer to the calculated segments object.
   */
  vector_r data_energies(int i) const {return dataEnergies_[i];};
  /*!
   * Returns a pointer to the calculated segments object.
   */
  vector_r data_segments(int i) const {return dataSegments_[i];};
  /*!
   * Returns a pointer to the calculated segments object.
   */
  vector_r data_segments_errors(int i) const {return dataSegmentsErrors_[i];};
  /*!
   * Returns a pointer to the calculated segments object.
   */
  vector_r calculated_segments(int i) const {return calculatedSegments_[i];};
  /*!
   * Returns a pointer to the calculated energies object.
   */
  vector_r calculated_energies(int i) const {return calculatedEnergies_[i];};
  /*!
   * Returns a pointer to the segments norms.
   */
  vector_r norms( ) const {return norms_;};
  /*!
   * Returns a pointer to the segments norms errors.
   */
  vector_r norms_errors( ) const {return normsErrors_;};
 
 private:

  // Configuration
  Config &configure_;
  EData *data_;
  CNuc *compound_;

  // Parameters
  std::vector<std::string> names_;
  std::vector<bool> fixed_;
  vector_r values_, transform_, norms_, normsErrors_;

  // Data
  std::vector<vector_r> dataEnergies_;
  std::vector<vector_r> dataSegments_;
  std::vector<vector_r> dataSegmentsErrors_;
  std::vector<vector_r> calculatedEnergies_;
  std::vector<vector_r> calculatedSegments_;

};

#endif