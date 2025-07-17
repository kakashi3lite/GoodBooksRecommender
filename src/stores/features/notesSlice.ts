// Notes slice
import { createSlice } from '@reduxjs/toolkit'

const notesSlice = createSlice({
  name: 'notes',
  initialState: { items: [] },
  reducers: {}
})

export default notesSlice.reducer
