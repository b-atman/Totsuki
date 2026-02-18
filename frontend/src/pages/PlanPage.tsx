/**
 * PlanPage - Meal Plan Generator
 * 
 * Features:
 * - Configure preferences (budget, time, protein, diet, cuisine)
 * - Generate 7-day meal plan
 * - View daily meals with details
 * - Shopping list with aggregated ingredients
 */

import { useState, useEffect } from 'react'
import { 
  Sparkles, 
  RefreshCw, 
  Clock, 
  DollarSign, 
  Dumbbell,
  ChevronDown,
  ChevronUp,
  ShoppingCart,
  Flame,
  UtensilsCrossed
} from 'lucide-react'
import { plannerApi } from '../api/planner'
import type { PlanRequest, PlanResponse, MealPlanDay } from '../types/planner'
import { CUISINE_LABELS, DIET_LABELS, DIFFICULTY_LABELS, DIFFICULTY_COLORS } from '../types/planner'

export default function PlanPage() {
  // Form state
  const [budget, setBudget] = useState<string>('')
  const [maxTime, setMaxTime] = useState<string>('60')
  const [proteinGoal, setProteinGoal] = useState<string>('')
  const [selectedDiets, setSelectedDiets] = useState<string[]>([])
  const [selectedCuisines, setSelectedCuisines] = useState<string[]>([])

  // Data state
  const [availableCuisines, setAvailableCuisines] = useState<string[]>([])
  const [availableDiets, setAvailableDiets] = useState<string[]>([])
  const [plan, setPlan] = useState<PlanResponse | null>(null)
  
  // UI state
  const [isLoading, setIsLoading] = useState(false)
  const [isLoadingOptions, setIsLoadingOptions] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showShoppingList, setShowShoppingList] = useState(false)

  // Load available cuisines and diets on mount
  useEffect(() => {
    async function loadOptions() {
      try {
        const [cuisines, diets] = await Promise.all([
          plannerApi.getCuisines(),
          plannerApi.getDiets(),
        ])
        setAvailableCuisines(cuisines)
        setAvailableDiets(diets)
      } catch (err) {
        console.error('Failed to load options:', err)
      } finally {
        setIsLoadingOptions(false)
      }
    }
    loadOptions()
  }, [])

  const handleGeneratePlan = async () => {
    setIsLoading(true)
    setError(null)
    
    try {
      const request: PlanRequest = {
        budget: budget ? parseFloat(budget) : undefined,
        max_time: maxTime ? parseInt(maxTime) : 60,
        protein_goal: proteinGoal ? parseFloat(proteinGoal) : undefined,
        diet_tags: selectedDiets.length > 0 ? selectedDiets : undefined,
        cuisine_preferences: selectedCuisines.length > 0 ? selectedCuisines : undefined,
      }
      
      const result = await plannerApi.generatePlan(request)
      setPlan(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate plan')
    } finally {
      setIsLoading(false)
    }
  }

  const toggleDiet = (diet: string) => {
    setSelectedDiets(prev => 
      prev.includes(diet) 
        ? prev.filter(d => d !== diet)
        : [...prev, diet]
    )
  }

  const toggleCuisine = (cuisine: string) => {
    setSelectedCuisines(prev => 
      prev.includes(cuisine)
        ? prev.filter(c => c !== cuisine)
        : [...prev, cuisine]
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Meal Planner</h1>
          <p className="text-gray-500 mt-1">
            Generate a personalized 7-day meal plan
          </p>
        </div>

        {/* Configuration Panel */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Your Preferences</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            {/* Budget */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Weekly Budget ($)
              </label>
              <div className="relative">
                <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="number"
                  value={budget}
                  onChange={(e) => setBudget(e.target.value)}
                  placeholder="No limit"
                  min="0"
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>
            </div>

            {/* Max Time */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Max Cooking Time (min)
              </label>
              <div className="relative">
                <Clock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <select
                  value={maxTime}
                  onChange={(e) => setMaxTime(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent appearance-none bg-white"
                >
                  <option value="30">30 min (Quick)</option>
                  <option value="45">45 min</option>
                  <option value="60">60 min</option>
                  <option value="90">90 min</option>
                  <option value="120">120 min</option>
                </select>
              </div>
            </div>

            {/* Protein Goal */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Protein Goal (g/meal)
              </label>
              <div className="relative">
                <Dumbbell className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="number"
                  value={proteinGoal}
                  onChange={(e) => setProteinGoal(e.target.value)}
                  placeholder="Any"
                  min="0"
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>
            </div>
          </div>

          {/* Diet Tags */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Dietary Requirements
            </label>
            <div className="flex flex-wrap gap-2">
              {isLoadingOptions ? (
                <span className="text-gray-400 text-sm">Loading...</span>
              ) : (
                availableDiets.map((diet) => (
                  <button
                    key={diet}
                    onClick={() => toggleDiet(diet)}
                    className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                      selectedDiets.includes(diet)
                        ? 'bg-primary-100 text-primary-700 border-2 border-primary-500'
                        : 'bg-gray-100 text-gray-600 border-2 border-transparent hover:bg-gray-200'
                    }`}
                  >
                    {DIET_LABELS[diet] || diet}
                  </button>
                ))
              )}
            </div>
          </div>

          {/* Cuisine Preferences */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Preferred Cuisines (optional)
            </label>
            <div className="flex flex-wrap gap-2">
              {isLoadingOptions ? (
                <span className="text-gray-400 text-sm">Loading...</span>
              ) : (
                availableCuisines.map((cuisine) => (
                  <button
                    key={cuisine}
                    onClick={() => toggleCuisine(cuisine)}
                    className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                      selectedCuisines.includes(cuisine)
                        ? 'bg-green-100 text-green-700 border-2 border-green-500'
                        : 'bg-gray-100 text-gray-600 border-2 border-transparent hover:bg-gray-200'
                    }`}
                  >
                    {CUISINE_LABELS[cuisine] || cuisine}
                  </button>
                ))
              )}
            </div>
          </div>

          {/* Generate Button */}
          <button
            onClick={handleGeneratePlan}
            disabled={isLoading}
            className="w-full md:w-auto inline-flex items-center justify-center gap-2 px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
          >
            {isLoading ? (
              <>
                <RefreshCw className="w-5 h-5 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <Sparkles className="w-5 h-5" />
                Generate Meal Plan
              </>
            )}
          </button>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg">
            {error}
            <button
              onClick={() => setError(null)}
              className="ml-4 text-red-500 hover:text-red-700 underline"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Generated Plan */}
        {plan && (
          <>
            {/* Summary Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
              <SummaryCard
                icon={DollarSign}
                label="Total Cost"
                value={`$${plan.summary.total_cost.toFixed(2)}`}
                color="green"
              />
              <SummaryCard
                icon={Dumbbell}
                label="Avg Protein"
                value={`${plan.summary.avg_protein_per_meal.toFixed(0)}g`}
                color="blue"
              />
              <SummaryCard
                icon={Flame}
                label="Total Calories"
                value={plan.summary.total_calories.toLocaleString()}
                color="orange"
              />
              <SummaryCard
                icon={Clock}
                label="Avg Time"
                value={`${plan.summary.avg_time_per_meal.toFixed(0)} min`}
                color="purple"
              />
            </div>

            {/* 7-Day Plan */}
            <div className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Your 7-Day Plan</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                {plan.days.map((day) => (
                  <DayCard key={day.day} day={day} />
                ))}
              </div>
            </div>

            {/* Shopping List */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
              <button
                onClick={() => setShowShoppingList(!showShoppingList)}
                className="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <ShoppingCart className="w-5 h-5 text-gray-600" />
                  <span className="font-semibold text-gray-900">
                    Shopping List ({plan.shopping_list.length} items)
                  </span>
                </div>
                {showShoppingList ? (
                  <ChevronUp className="w-5 h-5 text-gray-400" />
                ) : (
                  <ChevronDown className="w-5 h-5 text-gray-400" />
                )}
              </button>
              
              {showShoppingList && (
                <div className="border-t border-gray-200 p-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                    {plan.shopping_list.map((item, idx) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between py-2 px-3 bg-gray-50 rounded-lg"
                      >
                        <span className="text-gray-900 capitalize">{item.name}</span>
                        <span className="text-gray-500 text-sm">
                          {item.total_quantity} {item.unit}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </>
        )}

        {/* Empty State */}
        {!plan && !isLoading && (
          <div className="text-center py-16 bg-white rounded-xl border border-gray-200">
            <UtensilsCrossed className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No plan yet</h3>
            <p className="text-gray-500 max-w-md mx-auto">
              Configure your preferences above and click "Generate Meal Plan" to create your personalized 7-day meal plan.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

// =============================================================================
// Helper Components
// =============================================================================

function SummaryCard({ 
  icon: Icon, 
  label, 
  value, 
  color 
}: { 
  icon: React.ElementType
  label: string
  value: string
  color: 'green' | 'blue' | 'orange' | 'purple'
}) {
  const colorClasses = {
    green: 'bg-green-50 text-green-600',
    blue: 'bg-blue-50 text-blue-600',
    orange: 'bg-orange-50 text-orange-600',
    purple: 'bg-purple-50 text-purple-600',
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
      <div className={`inline-flex p-2 rounded-lg ${colorClasses[color]} mb-2`}>
        <Icon className="w-5 h-5" />
      </div>
      <p className="text-sm text-gray-500">{label}</p>
      <p className="text-xl font-semibold text-gray-900">{value}</p>
    </div>
  )
}

function DayCard({ day }: { day: MealPlanDay }) {
  const recipe = day.recipes[0]
  
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition-shadow">
      {/* Day Header */}
      <div className="bg-primary-50 px-4 py-2 border-b border-primary-100">
        <span className="font-semibold text-primary-700">{day.day_name}</span>
      </div>
      
      {/* Recipe Info */}
      <div className="p-4">
        <h3 className="font-medium text-gray-900 mb-2 line-clamp-2">{recipe.title}</h3>
        
        {/* Tags */}
        <div className="flex flex-wrap gap-1 mb-3">
          {recipe.cuisine_tags.slice(0, 2).map((tag) => (
            <span
              key={tag}
              className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs"
            >
              {CUISINE_LABELS[tag] || tag}
            </span>
          ))}
        </div>
        
        {/* Stats */}
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div className="flex items-center gap-1.5 text-gray-600">
            <Clock className="w-3.5 h-3.5" />
            <span>{recipe.time_minutes} min</span>
          </div>
          <div className="flex items-center gap-1.5 text-gray-600">
            <Dumbbell className="w-3.5 h-3.5" />
            <span>{recipe.protein_estimate}g</span>
          </div>
          <div className="flex items-center gap-1.5 text-gray-600">
            <Flame className="w-3.5 h-3.5" />
            <span>{recipe.calorie_estimate} cal</span>
          </div>
          <div className="flex items-center gap-1.5 text-gray-600">
            <DollarSign className="w-3.5 h-3.5" />
            <span>${recipe.estimated_cost.toFixed(2)}</span>
          </div>
        </div>
        
        {/* Difficulty */}
        <div className="mt-3 pt-3 border-t border-gray-100">
          <span className={`text-xs font-medium ${DIFFICULTY_COLORS[recipe.difficulty]}`}>
            {DIFFICULTY_LABELS[recipe.difficulty]}
          </span>
        </div>
      </div>
    </div>
  )
}
